# Evidence pinning — amendments rev 2 for `draft-krausz-verification-state-02`

**Status: DRAFT amendments for review. Not filed. Not implemented.**

**Replaces** `evidence-pinning-02-candidate2-amendments-2026-09-04.md` (sha256
`90c994e1f177…`), which stays on disk byte-unchanged. Two of its design choices are
**reversed**, not adjusted, and both reversals are recorded in full below rather than folded
into the text.

**Base:** `drafts/evidence-pinning-02-review-draft.md`, sha256
`9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096`, 14,469 bytes, 289 lines.
Verified live at the published raw URL: the bytes GitHub serves hash to that value.

**Review inputs seated in this revision.** Three reviewers, three independent mechanisms for
the same gap, converging on a design none of them proposed alone:

| Reviewer | Mechanism proposed | Where it landed |
|---|---|---|
| `poteshniy` | completeness *status*, parallel to kid-role `unknown`; partial must not be a reject | §4.3 step resolution, and the not-invalid rule at §4.1.3 |
| `giskard09` | move the *claim*, not the behaviour; plus a reader-side clause | §4.1.3 rationale, and §4.3 step (e) |
| `headlessoracle` | *possession*, not composition or consequence — pin what you received | §4.1.1, the normative core of this revision |

---

## Reversal 1 — `unpinned_reason` moves from OPTIONAL to REQUIRED

**Rev 1 said:** reason codes are OPTIONAL, MUST NOT be treated as a substitute for the
completeness rule, and their absence MUST NOT be a defect. The recorded reasoning was that
reason codes make an exclusion *inspectable*, which requires someone to inspect, while a
status change propagates without anyone auditing.

**That reasoning was correct about rev 1's design and wrong about this one.** It assumed the
reason code was a disclosure sitting beside the real mechanism. Under a possession-based
obligation the reason code **is** the mechanism: it is the issuer's signed assertion about
what it did or did not receive. An issuer that received bytes and declares
`no_content_returned` has not withheld a disclosure — it has signed a false statement.

The rev 1 enum was also wrong at the abstraction level. It named **world-causes**
(`paywall`, `robots_exclusion`, `size_limit`, `license_restriction`), which are facts about a
source. This revision names **possession states**, which are facts about the issuer's own
process. World-causes collapse into possession states — a paywall means no content bytes were
returned — and the world-cause enum let an issuer select a legitimate-sounding cause while
actually holding the bytes. The possession enum removes that move because the issuer is
signing over its own conduct, not characterising someone else's server.

**Credit:** `headlessoracle`, whose formulation this is.

## Reversal 2 — the `offline_recompute` payload member is dropped

**Rev 1 said:** add `offline_recompute` (`"available"` / `"unavailable"`) as a required member,
MUST track `fully_pinned`, with the mismatched combination malformed. The reasoning was that
`fully_pinned` reports a fact about the array while `offline_recompute` reports what the
receipt *claims*.

**Reversed for two reasons, the second of which is the stronger.**

First, the member is derivable. `source_count` and `pinned_count` are both required and both
inside the signed payload, so a reader already has the arithmetic. A required member that MUST
equal a function of two other required members is redundancy that can drift, and rev 1 needed
extra normative machinery — declaring the mismatch malformed — to police drift it introduced
itself. As `headlessoracle` put it: an enumerated completeness member adds nothing over the
counts unless it carries the consequence, so state the consequence and the counts do the rest.

Second, and this is the reason the member was misplaced rather than merely redundant:
**`poteshniy` asked for a status "parallel to kid-role `unknown`," and kid-role `unknown` is a
step resolution, not a payload member.** Rev 1 honoured the word "status" and missed the
analogy. Expressing the consequence as a §4.3 step resolution is more faithful to the
refinement that motivated it than the member ever was.

The consequence itself is unchanged and is now normative text in §4.3.

---

## 1. §2 Terminology — one correction

**Amend the `pinned` entry and add nothing else.** Finding 11 (`headlessoracle`): the member
name `pinnable` at review-draft l.92 names a *capability* where the member records a *fact*,
and `pinned` is the word §2 already defines.

> **`pinned`** is the term of art; the per-item member is named `pinned`, not `pinnable`. An
> evidence item is pinned when the receipt carries a digest of the retrieved content. An item
> carrying a URI alone is not pinned.

**Renames `pinnable` → `pinned` throughout §4.1.1 and §4.3.** This is a wire-format rename in
a draft that has not been filed, so no compatibility obligation attaches.

## 2. §4.1 `evidence_set` — two corrections, no new members

**No `offline_recompute` member** (Reversal 2). The member table is unchanged except:

**Finding 12** — set-level `retrieved_at` (l.71) and per-item `retrieved_at` (l.91) mean
different things and the set-level one is undefined. **Taken, by definition rather than
deletion:**

> `retrieved_at` at set level MUST equal the earliest per-item `retrieved_at` in `sources`. It
> is a convenience for readers sizing the age of the set and carries no independent meaning; a
> value that is not the earliest per-item value is a malformed receipt.

Defining it beats dropping it because a reader who wants the set's age should not have to walk
the array, and an undefined-but-present member is the worse of the three options.

**Finding 13** — §4.3 step (a) checks `pinned_count` against the pinned entries and
`fully_pinned` against the counts, but never checks `source_count` against `sources.length`.
**Taken**, in §4.3 below. He is right that a count disagreeing with its own array is the first
malformation an implementer will produce.

## 3. §4.1.1 `sources` entries — the possession rule

**This is the normative core of the revision.** Insert before the MUST NOT at review-draft
l.101.

> An issuer MUST pin every evidence item for which it received content bytes. `pinned` MAY be
> `false` **only** where no content bytes were received or retained for that item.
>
> Every item with `pinned: false` MUST carry an `unpinned_reason` from this domain:
>
> | Value | Meaning |
> |---|---|
> | `no_content_returned` | The retrieval attempt returned no content bytes. Covers refusal, paywall interception, robots exclusion, and transport failure alike — the receipt records that nothing arrived, not why. |
> | `content_not_retained` | Content bytes arrived and were discarded before a digest was computed. |
> | `provider_metadata_only` | The retrieval surface returned metadata about a resource without its content. |
>
> An item with `pinned: false` and no `unpinned_reason`, or with a value outside this domain,
> is a malformed receipt; gate decision = halt.
>
> An issuer that received content bytes for an item and declares any of these values has
> signed a false statement. **The format cannot verify possession from the receipt.** What it
> does is convert selective pinning from a permitted state into a lie — the same status as any
> other false statement a signed receipt could carry, and subject to the same consequences
> outside the format.

**Why possession and not composition.** A composition rule — pin every source that refutes
the verdict — cannot be written, because "refutes" is the issuer's own classification and an
issuer wanting to conceal a source classifies it as irrelevant. Policing that requires a third
party to re-retrieve and re-evaluate the evidence, which is the live dependency this whole
section exists to remove. Possession is different in kind: **whether bytes arrived is a fact
about the issuer's own process, not a judgment about a source.** It can therefore be stated
normatively without requiring anyone to check anything, and its falsification is a lie rather
than a defensible reading.

**Finding 14** — the no-normalization rule at l.94–99 must extend to `url`. **Taken:**

> The `url` carried in an entry MUST be the URI bytes used for retrieval, without
> normalization — no case folding, percent-encoding changes, query reordering, or trailing-slash
> adjustment. `url` bytes enter the leaf preimage per §4.1.2, so two verifiers holding one
> resource under two spellings would otherwise compute two roots for the same evidence.

**Finding 3, Q1** — content kind. **Taken as proposed:**

> | Member | Type | Required | Meaning |
> |---|---|---|---|
> | `content_kind` | string | yes when `pinned` is `true` | One of `snippet`, `excerpt`, `full_resource`. Names what the digest covers. |
> | `resource_sha256` | string | no | Digest of the full resource, where the full resource was also obtained. |
>
> `snippet_sha256` covers exactly the bytes that were judged. Two providers returning different
> snippets from one page produced different judgments, so different digests are correct and are
> not a defect. `resource_sha256` lets a reader tie a snippet to its resource where both were
> obtained, and its absence means only one was. **A full-resource digest as the only digest
> would pin something that was not judged**, and MUST NOT be substituted for `snippet_sha256`.

## 4. §4.1.2 `evidence_root` — two statements the text implies but does not make

**Finding 1** — the leaf preimage takes `snippet_sha256` as its 64 lowercase hex characters,
not as 32 raw bytes. The existing text says UTF-8, which implies it. **Taken; it wants saying:**

> In the leaf preimage, `snippet_sha256` is its **64 lowercase hexadecimal characters** encoded
> UTF-8, not the 32 raw bytes they represent. `url` is its UTF-8 bytes as carried, per §4.1.1.

**Finding 2** — a promoted odd entry keeps its rightmost position. **Taken:**

> A promoted entry retains its **rightmost position** at the next level. Promotion moves an
> entry up a level without changing its order relative to the pairs beside it.

## 5. §4.3 Verification Protocol — the consequence, and the reader-side rule

Replace step N's sub-steps with:

> a. Verify `source_count` equals the number of entries in `sources`; that `pinned_count` equals
>    the number of entries whose `pinned` is `true`; that `fully_pinned` is `true` if and only if
>    `pinned_count` equals `source_count` and `source_count` is greater than zero; that
>    set-level `retrieved_at` equals the earliest per-item value; and that every entry with
>    `pinned: false` carries an `unpinned_reason` from the §4.1.1 domain. Any inconsistency is a
>    malformed receipt; gate decision = halt.
>
> b. If `evidence_root` is non-null, recompute it from the `sources` entries per §4.1.2 and
>    compare. A mismatch is a malformed receipt; gate decision = halt. `evidence_root` MUST be
>    null when `pinned_count` is zero and MUST be non-null when `pinned_count` is greater than
>    zero; either violation is malformed.
>
> c. **When `fully_pinned` is `false`, this step resolves `unknown`, and the receipt MUST NOT be
>    presented as satisfying offline recomputation** — the verdict depended on content the
>    receipt does not commit to. This is the completeness consequence; it is a resolution of
>    this step, not a member of the payload.
>
> d. If the verifier holds candidate content for a pinned item, compute its SHA-256 and compare
>    with `snippet_sha256`. A mismatch resolves `unknown` for that item and MUST NOT halt. The
>    verifier's report SHOULD carry a per-item reason distinguishing `content_not_held` from
>    `content_differs`. **That distinction belongs in the report, never in the verdict domain**:
>    a verifier holding different bytes knows that its bytes differ and does not know why, and
>    widening the verdict domain to carry a fact the verifier cannot establish would undo the
>    narrowing this document has just done. Same shape as the coverage manifest — what did not
>    run is named beside the verdict, never folded into it. (Finding 5, Q3.)
>
> e. A receipt carrying no `evidence_set` resolves `unknown` for this step and MUST NOT fail it.
>    Receipts issued before this section existed remain valid.
>
> f. **A properly declared partial evidence set is not invalid and the receipt is not
>    malformed.** An implementation MUST NOT treat an `unknown` resolution under (c) as a
>    validity failure or a rejection. Partial pinning is unavoidable where no content bytes
>    were received, and a rule making declared partial sets invalid would push issuers to pin
>    nothing rather than declare honestly — strictly worse than the state it would close.
>    Note the precision: what is not invalid is a **declared** partial set. An unpinned item
>    with no reason is malformed under (a), and an issuer that possessed bytes and declared
>    otherwise has signed a false statement under §4.1.1.
>
> g. **A verifier MUST treat an `unknown` resolution under (c) as a distinct category and MUST
>    NOT present it as a weaker or partial form of a satisfied offline-recompute claim.** A
>    verifier that reports, displays, summarises, or forwards an outcome MUST carry the
>    distinction into whatever it emits. Collapsing the two — "verified, some sources unpinned" —
>    restores the laundering this section removes, by re-narrating an honest resolution as a
>    nearly-complete version of a stronger one.

**Step (g) is `giskard09`'s** and is unchanged from rev 1 in substance: a format-level
guarantee re-narrated in prose provides no guarantee. **Step (f)'s second half is new to this
revision** — under rev 1 every partial set was well-formed, so "partial is not invalid" needed
no qualifier. Under a possession obligation an undeclared partial set *is* malformed, and the
sentence has to say which is which or a reader takes the wrong half.

**Finding 4, Q2** — `evidence_root` inside the signed payload, without exception. **Taken,
with his observation recorded because it changes what the member is for:**

> `evidence_root` MUST be inside the signed payload. A root outside the signature is a pointer
> again, which is the condition §0 exists to close.
>
> With `sources` also inside the payload, the root adds no integrity the signature does not
> already provide. **Its value is disclosure**: it permits a later increment in which `sources`
> MAY be detached and the root retained, with inclusion proofs for the items disclosed. That
> increment is not specified here. The root is defined now in the shape that increment will
> need, which is why the construction is fixed and domain-separated despite being redundant
> against the signature today.

## 6. §5 — the limits section, three understatements

**Findings 8, 9, 10.** All three taken. The first is in the section's own opening sentence.

> - **Not that the source has not changed.** A pinned digest lets a later holder of bytes
>   determine whether they hold the bytes that were judged. It says **nothing** about whether
>   the source at that URI has since changed, and a reader will take the weaker sentence the
>   stronger way. (Replaces "and that it has not changed since" at l.183.)
> - **Not completeness of disclosure.** The set records what the issuer listed. §4.1.1 forbids
>   omitting a retrieved item, and **nothing in the receipt can detect an omission**. An issuer
>   can omit a source it retrieved and the format cannot see it; §4.1.1 makes that a false
>   statement rather than a permitted state, which is a different thing from making it
>   detectable.
> - **Not the time.** `retrieved_at` is an issuer assertion with no anchor, deliberately, per §8.
>   The digest therefore pins content as of a moment the issuer alone vouches for. An auditor in
>   2029 holds the content and does not hold the moment.
> - **Not unbiased selection.** The format does not establish that a pinned subset was chosen
>   without regard to the verdict. What §4.1.1 establishes is that leaving a possessed item
>   unpinned is a lie, and what §4.3 (c) establishes is that any partial set makes no
>   offline-recompute claim.

`headlessoracle`'s judgement on this section, recorded because it is the argument for stating
all four: say them and the section becomes the strongest part of the text rather than the part
someone else finds.

## 7. §5.x independence — unchanged

Declares a method identifier and does not define the method. Confirmed correct by
`headlessoracle`; no amendment.

## 8. §6 Conformance vectors — recut

**Removed:** `evi-partial-pinning-honest` (checks arithmetic only; certifies the gap rather
than catching it — `poteshniy` and `giskard09` independently), and rev 1's
`evi-recompute-claim-inconsistent-rejects` (no longer applicable; the member it policed is
dropped).

| id | designation | input | expect |
|---|---|---|---|
| `evi-root-order-independent` | CANONICAL ORDER | same two items, reversed | identical `evidence_root` |
| `evi-root-odd-promotion` | ODD NODE | three pinned items | root matches promote-not-duplicate, promoted entry rightmost |
| `evi-leaf-hex-not-raw` | LEAF PREIMAGE | one item, digest as 64 hex vs 32 raw bytes | roots differ; hex form is normative |
| `evi-snippet-change-changes-root` | BINDING | one snippet byte altered | `evidence_root` differs |
| `evi-url-normalization-changes-root` | BINDING | same resource, two URL spellings | roots differ; unnormalized bytes are normative |
| `evi-duplicate-url-distinct-digest` | CANONICAL ORDER | two items, same `url`, different `snippet_sha256` | deterministic order by `snippet_sha256`; stable root |
| `evi-unpinned-without-reason-rejects` | MALFORMED | `pinned: false`, no `unpinned_reason` | halt, malformed |
| `evi-unpinned-reason-outside-domain-rejects` | MALFORMED | reason value not in the §4.1.1 domain | halt, malformed |
| `evi-partial-resolves-unknown` | COMPLETENESS | 3 sources, 2 pinned with valid reason on the third | step resolves `unknown`; `must_not: ["valid"]` on the offline-recompute claim |
| `evi-declared-partial-is-not-invalid` | COMPLETENESS | same input | receipt core-valid, NOT malformed, MUST NOT halt |
| `evi-source-count-mismatch-rejects` | MALFORMED | `source_count` disagrees with `sources.length` | halt, malformed |
| `evi-count-inconsistency-rejects` | MALFORMED | `pinned_count` disagrees with pinned entries | halt, malformed |
| `evi-root-with-zero-pinned-rejects` | MALFORMED | non-null root, `pinned_count` zero | halt, malformed |
| `evi-nonzero-pinned-null-root-rejects` | MALFORMED | null root, `pinned_count` greater than zero | halt, malformed |
| `evi-root-mismatch-rejects` | MALFORMED | root not recomputable from sources | halt, malformed |
| `evi-content-mismatch-unknown` | UNKNOWN | verifier holds different bytes | `unknown`, MUST NOT halt, per-item reason `content_differs` |
| `evi-content-not-held-unknown` | UNKNOWN | verifier holds no candidate bytes | `unknown`, per-item reason `content_not_held` |
| `evi-absent-unknown` | ADDITIVE | no `evidence_set` | `unknown`, MUST NOT halt |
| `evi-empty-root-null` | EMPTY | zero pinned items | `evidence_root` null |

**`evi-partial-resolves-unknown` and `evi-declared-partial-is-not-invalid` MUST be adopted as a
pair.** The first alone is satisfiable by rejecting every partial set, which is the failure
§4.3 (f) exists to prevent. Neither is sufficient alone.

## 9. §8 — cross-format verifier citation

Cite by version and integrity, and by tag:

> `@headlessoracle/receipt-verify@0.1.2`, integrity
> `sha512-M8I9mgXCsOoi1i9egEOapAp1mp8xdImkAg56BtqQZ3R9tlA7bQk5E6QllvFcDPIMZH8ty6lR3enOVZDa5mIDlQ==`,
> published 2026-09-04T20:18:21Z. Repository `github.com/LembaGang/receipt-verify`, tag
> `v0.1.2`.

Verified against the registry and the repository, not taken from the message: the integrity
string matches the published dist exactly, `0.1.2` is the `latest` tag, and 59 of 59 sampled
commits carry verified signatures. The published tarball was compared file-for-file against a
fresh build of the tagged commit on a second machine and found identical — a check `0.1.1`
could not pass, which is the reason this supersedes it.

**Citation precision — `v0.1.2` is an annotated tag.** The tag object is
`7eaa8a46266604a70fdaa77ad8516d2f09baee6b` and it dereferences to commit
`1c3452fe9a8109616481dad75dacb312517bf47f`. Citing "tag `v0.1.2`" is unambiguous. **A bare
SHA must say which object it names**, because the two differ and a reader given one cannot tell
which was meant.

**Row scope, unchanged and not to be widened.** The implementer's own row states it is not a
cross-implementation result and establishes nothing about any other implementation of
`verification.*`. Those words stay. The row makes no byte-for-byte claim about canonical bytes,
and per his written instruction it is counted for what the row says and no more.

## 10. §9 — anchoring stays out

Confirmed by `headlessoracle`; unchanged from the review draft. A Merkle root over receipts is
a separate mechanism and a later increment, and anchoring receipts that pin URIs rather than
content would commit to pointers.

---

## Findings ledger — all 14, each taken or answered

| # | Finding | Disposition |
|---|---|---|
| 1 | Leaf preimage: `snippet_sha256` as 64 hex chars, not 32 raw bytes | **Taken** — §4.1.2, plus vector `evi-leaf-hex-not-raw` |
| 2 | Promoted odd entry keeps rightmost position | **Taken** — §4.1.2, folded into `evi-root-odd-promotion` |
| 3 | Q1: `content_kind` enum plus optional `resource_sha256` | **Taken as proposed** — §4.1.1 |
| 4 | Q2: root inside signed payload; value is disclosure, not integrity | **Taken**, with the disclosure rationale recorded — §4.1.2 note |
| 5 | Q3: keep `unknown`; per-item `content_not_held` vs `content_differs` in the report | **Taken** — §4.3 (d), plus two UNKNOWN vectors |
| 6 | Possession rule: pin what you received; mandatory `unpinned_reason` | **Taken as the normative core** — §4.1.1. Reverses rev 1's OPTIONAL reason codes |
| 7 | Drop the enumerated completeness member; state the consequence | **Taken** — Reversal 2; consequence now §4.3 (c) |
| 8 | "has not changed since" overclaims what a digest gives | **Taken** — §5 bullet 1, replacing l.183 |
| 9 | Section names completeness of retrieval, not of disclosure | **Taken** — §5 bullet 2 |
| 10 | `retrieved_at` unanchored; auditor holds content, not the moment | **Taken** — §5 bullet 3 |
| 11 | `pinnable` names a capability; `pinned` is the defined term | **Taken** — rename throughout |
| 12 | Set-level `retrieved_at` undefined | **Taken by definition, not deletion** — earliest per-item value, mismatch malformed |
| 13 | Step (a) never checks `source_count` against `sources.length` | **Taken** — §4.3 (a), plus `evi-source-count-mismatch-rejects` |
| 14 | No-normalization rule must extend to `url` | **Taken** — §4.1.1, plus `evi-url-normalization-changes-root` |

Nothing was answered-but-declined. The only place this revision departs from the read is
finding 12, where deletion was offered as an alternative and definition was chosen instead;
the reason is stated at §2 above.

## Open questions

**Q-a — is `content_kind` required only when pinned?** Drafted as required when `pinned` is
`true`, absent otherwise. An unpinned item has no digest, so nothing to describe. Flagged
because a reader may expect the member to describe *what was sought* rather than what was
digested, which would make it required on every item.

**Q-b — is a fourth possession value needed?** The read invited one "if you have a real fourth
case." Three are drafted. A candidate is a retrieval that returned content bytes the issuer was
contractually barred from retaining, which is `content_not_retained` in mechanism and different
in kind. Not added without a real case, because an enum value nobody emits is worse than an
enum that is one case short.

**Q-c — does the detached-sources increment need a version marker now?** §4.1.2 is defined in
the shape that increment will need. Whether `evidence_set_version` must change when `sources`
becomes detachable is unresolved, and it is the kind of thing that is cheaper to settle before
the shape ships than after.
