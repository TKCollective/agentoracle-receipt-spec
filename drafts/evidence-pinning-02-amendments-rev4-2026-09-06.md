# Evidence pinning — amendments rev 4 for `draft-krausz-verification-state-02`

**Status: DRAFT amendments for review. Not filed. Not implemented.**

**Replaces** `evidence-pinning-02-amendments-rev3-2026-09-04.md` (sha256
`d770436219038098d1ea8c9dad08b96d7939eec5207de8556138ffe500dc1216`, 9,313 bytes, 162 lines),
which stays on disk byte-unchanged. Rev 3 replaced rev 2
(`a957802a4ed4d5a4097e2066fd0be4cbc5bf5d777ebbd5809e47f3bd4637bf74`), also unchanged.

**Base:** `drafts/evidence-pinning-02-review-draft.md`, sha256
`9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096`, 14,469 bytes, 289 lines.

**Bases re-derived at build time**, not carried from rev 3's header: the review draft and rev 3
were both fetched from `TKCollective/agentoracle-receipt-spec` at HEAD
`49b7d039576b17e39dd707c9f223de5670c9be86` and compared byte-for-byte against the local
copies. Both identical. Per
`a_check_that_cannot_distinguish_states_is_not_a_check.md`: a digest quoted from a previous
revision's header is not a derived digest.

**New filename per `semantics_change_new_filename.md`.** This revision widens the leaf
preimage, forbids a state rev 3 permitted, and raises a SHOULD to a MUST. Three semantics
changes; rev 3 and rev 4 are not interchangeable in any citation.

---

## ⚠ Breaking change notice — read before adopting

**The leaf preimage widens, and the domain-separation prefix moves from
`ao-evidence-leaf-v1` to `ao-evidence-leaf-v2`.** Every `evidence_root` computed under rev 3
or the review draft differs from the root computed under this revision over the same evidence.

This is deliberate and it is cheaper now than later. The root's only stated purpose (§4.1.2,
Finding 4) is the future increment in which `sources` MAY be detached and inclusion proofs
disclose individual items. In that increment the current preimage cannot do its job — see
Finding 15. Widening the preimage after the shape circulates invalidates every issued
receipt; widening it now regenerates six conformance fixtures.

**No published fixture is invalidated, because none exists.** No concrete `evidence_root`
value has ever been published for this section: every vector expectation in rev 2 is
*relational* ("identical", "differs", "roots differ"), and a relational assertion is invariant
under a change of preimage or prefix. Exactly one vector expectation changes, and it changes
because of the sort key in 15c rather than the preimage in 15a. See the vector changelog.

---

## Provenance of this revision

`headlessoracle` re-read rev 2 whole on `ebd8c13` with `49b7d03` on top and returned eight
items, none of them a reversal of anything previously taken, with items 1 and 2 identified as
pre-filing blockers. All eight are taken. All eight were verified against the base text rather
than accepted from the summary; the verification results are recorded per finding.

**Four consequences were derived on this side and confirmed as consequences rather than new
design**: the canonical-order sort key (Finding 15c), Q-a closing by construction (Finding
21), Finding 19's resolution following from Reversal 2, and Finding 20's prohibition following
from §4.3 (e) already housing the state.

**Two interactions surfaced during drafting that neither review produced.** Both are recorded
in full rather than folded in silently, because each changes what a reviewer holding the
eight-item list should expect to see:

- **The prefix bump (Finding 15b).** A widened preimage under an unchanged prefix leaves two
  incompatible constructions wearing one label, which contradicts the base's own
  domain-separation paragraph. The prefix must move with the preimage. This also answers Q-c:
  the leaf prefix *is* the version marker for the preimage, so no separate
  `evidence_set_version` bump is required for this change.
- **Item 6 dissolves item 4(ii) (Finding 18b).** Once `source_count` MUST exceed zero, the
  malformation "`fully_pinned` true with `source_count` zero" is unreachable — the receipt is
  already malformed at the `source_count` check. The vector requested for 4(ii) would be
  refused by a different rule than the one it targets, which is not a test of that rule. It is
  replaced by the empty-set vector rather than written as requested.

---

## Findings 15–22 — the re-read

### Finding 15 — the leaf preimage binds `url` and the digest and nothing else

**Verified.** Base l.113: `leaf = SHA-256( "ao-evidence-leaf-v1" || 0x00 || url || 0x00 ||
snippet_sha256 )`. `content_kind` (added rev 2, §4.1.1) and per-item `retrieved_at` (base
l.91) are both unbound. Harmless while `sources` sits inside the signed payload; unsound in the
detached increment, where a reader holding an inclusion proof cannot tell whether the digest
covers a snippet or a full resource.

**`pinned` needs no binding — corrected against the re-read.** Base l.107 states the root is
"over the pinned items only. Unpinned items contribute nothing," and l.110 says "For each
pinned item." A leaf exists only for a pinned item, so `pinned: true` is implied by the
existence of a leaf and carries into any inclusion proof. It is unbound **by construction**,
not by omission. Two of the three members named in the re-read need fixing; the third is
already sound.

**Option (a) taken, not (b).** Reserving a version bump for a later widening makes the eventual
break legal without making the increment sound; the root would ship unable to perform its one
stated function. Widened now.

#### 15a — replacement §4.1.2 leaf construction

> **Leaf.** For each pinned item, in the canonical order defined below:
>
> ```
> leaf = SHA-256( "ao-evidence-leaf-v2" || 0x00 || url || 0x00 || snippet_sha256
>                 || 0x00 || content_kind || 0x00 || retrieved_at )
> ```
>
> where `url`, `snippet_sha256`, `content_kind`, and `retrieved_at` are their UTF-8 bytes as
> carried in the entry, and `||` is concatenation. No member may contain an octet `0x00`:
> `url` is a URI, `snippet_sha256` is lowercase hex, `content_kind` is drawn from a closed
> enumeration, and `retrieved_at` is an RFC 3339 timestamp. Delimiter injection is therefore
> unreachable and no length prefixes are required.
>
> **Every member the preimage binds MUST also appear in the canonical sort key of §4.1.2, and
> the sort key MUST bind no member the preimage does not.** A bound member absent from the sort
> key leaves the order of two entries differing only in that member undefined, and therefore
> the root non-deterministic. A sort member absent from the preimage orders leaves by a value
> the leaf does not commit to. Any future widening of the preimage MUST extend the sort key in
> the same revision.

#### 15b — the prefix moves to `v2` (consequence, requires ratification)

The base's domain-separation paragraph (l.135) states the prefixes "ensure a leaf hash can
never be reinterpreted as an interior node, and that an evidence root can never collide with
any other hash tree defined by this document or composed alongside it." A widened preimage
under the prefix `ao-evidence-leaf-v1` produces a second, incompatible construction bearing a
label that already denotes the first. A verifier given a leaf cannot determine which
construction to apply.

`ao-evidence-node-v1` is **unchanged** — the interior-node construction is untouched.

**Effect on Q-c:** the leaf prefix is the preimage's version marker. Q-c asked whether the
detached-sources increment needs `evidence_set_version` to change. For the preimage, it does
not: `ao-evidence-leaf-v2` already discriminates. Q-c is closed for this change and remains
open only for members outside the preimage.

#### 15c — replacement canonical-order rule (consequence)

The re-read did not reach this, and it is the reason the item as written would have shipped a
non-deterministic root. Base l.130 sorts by `url`, then `snippet_sha256`. Under 15a two
entries may share both and differ in `content_kind` or `retrieved_at`, producing different
leaves in undefined order.

> **Canonical order.** Leaves are sorted ascending by `url`; where two entries share a `url`,
> by `snippet_sha256`; where they share both, by `content_kind`; and where they share all
> three, by `retrieved_at`. All four comparisons are bytewise over the UTF-8 encoding of the
> member as carried in the entry. The sort key is exactly the set of members bound by the leaf
> preimage, so two entries compare equal on the key only if their leaves are identical, in
> which case their order cannot affect the root. Sorting makes the root independent of
> retrieval rank, so two verifiers who retrieved the same evidence in different orders compute
> the same root.

### Finding 16 — `encoded UTF-8` on the content digest

**Verified, and it is an interoperability defect rather than an imprecision.** Base l.94–95
reads "computed over the retrieved content **exactly as received**, encoded UTF-8" — the two
clauses contradict each other. A resource that is not text has no encoding step, and rev 3's
own §4.1.1 clarifier says "the content bytes **as received**," which conflicts with the base
sentence rev 3 does not amend. Two conformant verifiers, one transcoding and one not, compute
different digests for the same resource. `content_kind: full_resource` explicitly contemplates
non-snippet content, which may be binary.

**Amend base l.94–98:**

> `snippet_sha256` is computed over the retrieved content **exactly as received** — the octet
> sequence as it arrived — with no transcoding, trimming, whitespace collapsing, case folding,
> or Unicode normalization. **There is no character-encoding step: the digest is over bytes,
> not over text.** A resource that is not text has no encoding to apply, and a verifier that
> transcodes before hashing computes a different digest from one that does not. Any
> transformation applied before hashing makes the digest unreproducible by a third party
> holding the same bytes, which defeats the purpose of carrying it.

**UTF-8 is retained where it belongs and both uses are correct as written**: base l.116, the
UTF-8 bytes of `url` and the hex characters of `snippet_sha256` inside the leaf preimage
(extended to four members by 15a); and base l.131, the bytewise comparison over UTF-8 in the
canonical order rule (extended to four comparisons by 15c). Neither is amended for this
finding.

### Finding 17 — §4.3 (d) SHOULD contradicts the two UNKNOWN vectors

**Verified.** Rev 2 §4.3 (d): "The verifier's report SHOULD carry a per-item reason." Vectors
`evi-content-mismatch-unknown` and `evi-content-not-held-unknown` both expect the per-item
reason. A verifier exercising the SHOULD's permission fails both.

**Resolved as MUST**, not by weakening the vectors.

> d. If the verifier holds candidate content for a pinned item, compute its SHA-256 and compare
>    with `snippet_sha256`. A mismatch resolves `unknown` for that item and MUST NOT halt. The
>    verifier's report **MUST** carry a per-item reason distinguishing `content_not_held` from
>    `content_differs`. **That distinction belongs in the report, never in the verdict domain**:
>    a verifier holding different bytes knows that its bytes differ and does not know why, and
>    widening the verdict domain to carry a fact the verifier cannot establish would undo the
>    narrowing this document has just done. Same shape as the coverage manifest — what did not
>    run is named beside the verdict, never folded into it.

**Rationale for MUST rather than dropping the vectors' expectation.** Step (g) requires a
verifier to carry the (c) distinction into whatever it emits. With (d) optional, a verifier
satisfies (g) while emitting a bare `unknown` carrying no per-item reason, and a reader cannot
tell whether the verifier lacked bytes or held **different** bytes. That is the same collapse
(g) forbids, one level down. The MUST is what makes (g) operative at item level; vector
consistency is the lesser reason.

### Finding 18 — malformations shipping with no known-bad input

**Verified for all three.** None has a vector in the rev 2 table.

#### 18a — set-level `retrieved_at` not the earliest per-item value

Finding 12 declares it malformed and §4.3 (a) checks it. Vector added:
`evi-set-retrieved-at-not-earliest-rejects`.

#### 18b — `fully_pinned` true with `source_count` zero: NOT written as requested

Base l.74 already defines `fully_pinned` as true "if and only if `pinned_count` equals
`source_count` and `source_count` is greater than zero," and §4.3 (a) checks it. The
malformation is real under rev 3.

**It is unreachable under rev 4.** Finding 20 requires `source_count` greater than zero, so a
receipt with `source_count: 0` is malformed at that check before `fully_pinned` is evaluated.
A vector whose input is refused by a rule other than the one it targets tests nothing about the
targeted rule. Replaced by `evi-empty-set-rejects` (Finding 20).

The `fully_pinned` iff-clause is **retained unchanged** — it remains correct, and removing the
`source_count > 0` conjunct would make `fully_pinned` vacuously true on a set Finding 20
forbids.

#### 18c — `content_kind` absent when `pinned` is true, with the consequence stated

The rev 2 member table says "required when `pinned` is `true`" and no sentence states what
happens when it is missing. Every other required-member violation in this document says
malformed-and-halt.

**Add to §4.3 (a):**

> ... and that every entry with `pinned: true` carries a `content_kind` from the §4.1.1
> enumeration. Any inconsistency is a malformed receipt; gate decision = halt.

**The failure is also self-enforcing.** `content_kind` enters the leaf preimage per 15a, so its
absence makes the leaf uncomputable and step (b)'s root recomputation cannot be performed at
all. The explicit check in step (a) exists so that the diagnostic names the missing member
rather than reporting a root mismatch, which would send an implementer looking in the wrong
place. Vector added: `evi-content-kind-absent-when-pinned-rejects`.

### Finding 19 — `content_kind: full_resource` and `resource_sha256`

**Verified: the rev 2 table admits both readings.** Resolved by this document's own precedent
rather than by a new design choice. Reversal 2 dropped `offline_recompute` because "a required
member that MUST equal a function of two other required members is redundancy that can drift."
When `content_kind` is `full_resource`, `snippet_sha256` already **is** the digest of the full
resource, so a `resource_sha256` required to equal it is that same pattern.

> `resource_sha256` MUST be absent when `content_kind` is `full_resource`. In that case
> `snippet_sha256` is already the digest of the full resource, and a second member carrying the
> same value is redundancy that can drift. Where `content_kind` is `snippet` or `excerpt`,
> `resource_sha256` MAY be present and, when present, is the digest of the full resource from
> which the judged bytes were taken. An entry carrying `content_kind: full_resource` together
> with `resource_sha256` is a malformed receipt; gate decision = halt.

Vector added: `evi-resource-sha256-with-full-resource-rejects`.

### Finding 20 — the empty set

**Verified, and it is the sharpest of the eight.** With `source_count` zero: `fully_pinned` is
false by definition, `evidence_root` is null by base l.139, and set-level `retrieved_at` under
Finding 12 is "the earliest per-item value" over an empty array — undefined, so §4.3 (a) cannot
be evaluated as written. §4.3 (c) then resolves `unknown`, whose stated meaning is "the verdict
depended on content the receipt does not commit to." **A receipt that names no sources is not
partial**, and routing it to `unknown` launders a distinct state into the partial-set state —
the collapse this document exists to prevent.

**Forbidden rather than defined**, because §4.3 (e) already houses the state: a receipt
carrying no `evidence_set` resolves `unknown` and MUST NOT fail. Defining the empty-present set
would create a second representation of one state, which is the ambiguity removed everywhere
else in this text.

> A present `evidence_set` MUST carry at least one entry in `sources`, and `source_count` MUST
> be greater than zero. An issuer with no sources to report MUST omit `evidence_set` entirely;
> §4.3 (e) resolves that case as `unknown` without failing it. An `evidence_set` present with
> `source_count` zero is a malformed receipt; gate decision = halt.
>
> **Zero pinned items remains legal and is not an empty set.** An `evidence_set` carrying three
> entries, none pinned, each with an `unpinned_reason` from the §4.1.1 domain, is well-formed;
> its `evidence_root` is `null` per §4.1.2; its `fully_pinned` is `false`; and §4.3 (c) resolves
> `unknown`. The prohibition is on an evidence set that names no sources, never on one that pins
> none.

Base l.139–140 ("When `pinned_count` is zero, `evidence_root` MUST be `null`") is **unchanged**
and continues to govern the legal zero-pinned case. Vector added: `evi-empty-set-rejects`.
`evi-empty-root-null` is retained unchanged — its input is zero *pinned*, not zero *sources*.

### Finding 21 — Q-a closes by construction (consequence)

The re-read holds Q-a as drafted: `content_kind` required when pinned, absent otherwise,
because an unpinned item has nothing to describe. That reasoning is correct and 15a makes it
structural.

With `content_kind` in the leaf preimage, it is **required** on every pinned item because the
leaf is uncomputable without it, and **absent** on every unpinned item because unpinned items
generate no leaf. Q-a is no longer a judgement about reader expectation; it is a consequence of
the construction. Recorded as closed rather than carried forward as open.

A reader who expects `content_kind` to describe *what was sought* rather than what was digested
is answered directly: the member is an input to a digest commitment, so it can only describe
what was digested.

### Finding 22 — the `59 of 59` citation

**Verified independently, and the re-read is right that the current wording understates a
stronger true claim.** "Sampled" implies a subset; the check was exhaustive over the history at
that commit. Re-derived at build time: the repository stands at **65 commits** on its default
branch today, and `6a94549` resolves with committer date `2026-09-04T20:25:08Z`. Tag `v0.1.2`
is confirmed an annotated tag object `7eaa8a46266604a70fdaa77ad8516d2f09baee6b`, so rev 2's
citation-precision paragraph stands unchanged.

**Amend the §8 verification sentence:**

> Verified against the registry and the repository, not taken from the message: the integrity
> string matches the published dist exactly, `0.1.2` is the `latest` tag, and **59 of 59
> commits — the whole history at `6a94549` on 4 September 2026 — carry verified signatures.**
> The repository has advanced since that commit; the count is stated as of the commit named.
> The published tarball was compared file-for-file against a fresh build of the tagged commit
> on a second machine and found identical — a check `0.1.1` could not pass, which is the reason
> this supersedes it.

### Finding 23 — the §5 cross-reference

**Verified as genuinely ambiguous, and the number differs between the two documents.** §5
bullet 3 reads "`retrieved_at` is an issuer assertion with no anchor, deliberately, per §8." In
the review draft's own numbering, **§8 is "What this does not include, deliberately"** (base
l.281) and its first bullet is "No anchoring" — so the reference is correct against the base.
Rev 2's section headers assert draft §8 is the cross-format verifier citation and §9 is
anchoring, under which the reference is wrong.

**Resolved by naming, not renumbering**, because a numbered cross-reference in a draft whose
sections are still moving will break again:

> - **Not the time.** `retrieved_at` is an issuer assertion with no anchor, deliberately — see
>   the exclusions section, "What this does not include, deliberately," whose first bullet
>   keeps anchoring out of scope. The digest therefore pins content as of a moment the issuer
>   alone vouches for. An auditor in 2029 holds the content and does not hold the moment.

**Open for the filing editor, not resolvable here:** the section *number* must be fixed against
the numbering of the filed draft, which differs between the review draft (§8) and rev 2's
assumption (§9). The named form above is correct under either.

---

## Vector changelog

### Recomputed on materialization — not regenerated, and nothing is invalidated

**Verified before writing this section: no concrete root value has ever been published.** The
only 64-character hex strings in the evidence-pinning corpus are document digests — the filed
draft-01 (`22c5ce26…`), the review draft, rev 2, and rev 3. The rev 2 vector table carries
**relational** expectations only.

Five of the six root-bearing vectors are therefore **unchanged in expectation**, because a
relational assertion does not depend on the prefix or the preimage membership:

| id | expectation | status under v2 |
|---|---|---|
| `evi-root-order-independent` | identical `evidence_root` | holds unchanged |
| `evi-root-odd-promotion` | root matches promote-not-duplicate, promoted entry rightmost | holds unchanged |
| `evi-leaf-hex-not-raw` | roots differ; hex form is normative | holds unchanged |
| `evi-snippet-change-changes-root` | `evidence_root` differs | holds unchanged |
| `evi-url-normalization-changes-root` | roots differ; unnormalized bytes are normative | holds unchanged |

**One expectation is restated, for the sort key and not for the preimage:**

| id | rev 2 expectation | rev 4 expectation |
|---|---|---|
| `evi-duplicate-url-distinct-digest` | "deterministic order by `snippet_sha256`; stable root" | "deterministic order by the four-term key of §4.1.2; stable root" — the two-term description is incomplete under 15c |

**What the widening actually costs.** When the fixture set is materialized with concrete inputs
and computed roots — which filing requires and which has not been done — those values are
computed under `ao-evidence-leaf-v2` from the outset. There is no prior published value to
supersede and no reader holding a value that will stop matching. The cost of 15a is paid in
work not yet done, not in work invalidated.

**Correction of record.** An earlier draft of this section stated that six fixtures regenerate
and instructed readers holding rev 3 fixtures to expect mismatches. No such fixtures exist and
no reader holds one; the statement was false and is withdrawn here rather than carried into
review.

### Added — eight vectors

| id | designation | input | expect |
|---|---|---|---|
| `evi-leaf-binds-content-kind` | LEAF PREIMAGE | two sets identical but for `content_kind` on one entry | `evidence_root` differs |
| `evi-leaf-binds-retrieved-at` | LEAF PREIMAGE | two sets identical but for per-item `retrieved_at` | `evidence_root` differs |
| `evi-order-tiebreak-content-kind` | CANONICAL ORDER | two entries sharing `url` and `snippet_sha256`, differing `content_kind`, supplied in both orders | identical `evidence_root` both ways |
| `evi-order-tiebreak-retrieved-at` | CANONICAL ORDER | two entries sharing `url`, `snippet_sha256`, `content_kind`, differing `retrieved_at`, both orders | identical `evidence_root` both ways |
| `evi-set-retrieved-at-not-earliest-rejects` | MALFORMED | set-level `retrieved_at` later than the earliest per-item value | halt, malformed |
| `evi-content-kind-absent-when-pinned-rejects` | MALFORMED | entry with `pinned: true` and no `content_kind` | halt, malformed, diagnostic names the missing member rather than a root mismatch |
| `evi-resource-sha256-with-full-resource-rejects` | MALFORMED | `content_kind: full_resource` together with `resource_sha256` | halt, malformed |
| `evi-empty-set-rejects` | MALFORMED | `evidence_set` present, `sources` empty, `source_count: 0` | halt, malformed |

### Not written, and why

`evi-fully-pinned-zero-sources-rejects`, requested as item 4(ii). Unreachable under Finding
20: `source_count: 0` is refused at the source-count check before `fully_pinned` is evaluated,
so the vector would be refused by a rule other than the one it targets. Replaced by
`evi-empty-set-rejects`. See Finding 18b.

### Retained unchanged — nine vectors

`evi-unpinned-without-reason-rejects`, `evi-unpinned-reason-outside-domain-rejects`,
`evi-partial-resolves-unknown`, `evi-declared-partial-is-not-invalid`,
`evi-source-count-mismatch-rejects`, `evi-count-inconsistency-rejects`,
`evi-root-with-zero-pinned-rejects`, `evi-nonzero-pinned-null-root-rejects`,
`evi-root-mismatch-rejects`, `evi-absent-unknown`, `evi-empty-root-null`.

`evi-content-mismatch-unknown` and `evi-content-not-held-unknown` are unchanged in expectation;
Finding 17 raises the normative text to meet them rather than the reverse.

**The pair rule stands.** `evi-partial-resolves-unknown` and `evi-declared-partial-is-not-invalid`
MUST be adopted together; the first alone is satisfiable by rejecting every partial set.

---

## Findings ledger — 15–23

| # | Finding | Disposition |
|---|---|---|
| 15 | Leaf preimage binds `url` and digest only; `content_kind` and `retrieved_at` unbound | **Taken, option (a)** — preimage widened, §4.1.2. `pinned` needs no binding, by construction |
| 15b | Widened preimage requires the domain prefix to move | **Consequence, requires ratification** — `ao-evidence-leaf-v2`. Also closes Q-c for the preimage |
| 15c | Sort key must cover exactly the bound members | **Consequence** — four-term canonical order; invariant stated normatively |
| 15d | No fixture is invalidated; five expectations hold, one restated for the sort key | **Consequence, verified** — no concrete root was ever published; earlier "six regenerate" claim withdrawn |
| 16 | `encoded UTF-8` on the content digest is an interop defect | **Taken** — struck from the content digest, retained in preimage and sort comparison |
| 17 | §4.3 (d) SHOULD contradicts both UNKNOWN vectors | **Taken as MUST** — with the step (g) argument in the rationale |
| 18a | Set-level `retrieved_at` malformation has no vector | **Taken** — vector added |
| 18b | `fully_pinned` true with `source_count` zero has no vector | **Not written** — unreachable under Finding 20; replaced by `evi-empty-set-rejects` |
| 18c | `content_kind` absent when pinned: no consequence, no vector | **Taken** — malformed-and-halt, stated as self-enforcing; vector added |
| 19 | `full_resource` + `resource_sha256` ambiguous | **Taken** — MUST be absent, per Reversal 2's own rule |
| 20 | The empty set | **Taken by prohibition** — `source_count` > 0 required; zero-pinned explicitly preserved |
| 21 | Q-a | **Closed by construction** under 15a, not carried forward |
| 22 | `59 of 59 sampled commits` | **Taken** — exhaustive and dated; 65 today, re-derived |
| 23 | §5 cross-reference `per §8` | **Taken by naming**; the number is left to the filing editor |

Findings 1–14 stand as filed in rev 2, except Finding 6 as amended by rev 3 and Finding 3 as
extended by 15a and 19. Both rev 2 reversals stand. Everything the re-read confirmed holds:
the two reversals and their reasons, Finding 12 by definition, the false-statement paragraph on
the two-value domain, steps (f) and (g), the four §5 limits, the pair rule, and the row scope
sentence as written.

## Open questions

- **Q-a** — **closed** by Finding 21, by construction.
- **Q-b** — closed by rev 3. No candidate for a third possession value has appeared in either
  review. Additive if one does.
- **Q-c** — **closed for the leaf preimage** by 15b: the prefix is the version marker. Remains
  open only for members outside the preimage, should the detached increment require any.

## What this revision does not settle

- The §5 cross-reference **number** (Finding 23), which depends on the filed draft's numbering.
- Whether the detached-sources increment needs a marker for non-preimage members (Q-c residue).
- **The fixture set itself, which does not yet exist.** This document specifies inputs and
  relational expectations; it does not materialize concrete entries or compute roots. The set
  must be built under `ao-evidence-leaf-v2` and cross-checked before filing, per the project's
  standing conformance discipline. Note precisely what that discipline requires: agreement
  between two implementations **written by the same party** is a cross-language check and
  catches language-specific defects. It is **not** an independent implementation and MUST NOT
  be described as one. Independence means built from the specification text alone by a party
  with no access to our implementation — which for this section means Michael or Pablo, not a
  second file in this repository.
