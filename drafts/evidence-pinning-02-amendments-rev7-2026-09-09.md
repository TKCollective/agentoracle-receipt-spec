# Evidence pinning — amendments rev 7 for `draft-krausz-verification-state-02`

**Status: DRAFT amendments for review. Not filed. Not implemented.**

**Replaces** `evidence-pinning-02-amendments-rev6-2026-09-08.md` (sha256
`d62ded37dcf63f541e5b670b0cc0f7876e04a182064eb06a32af0037effaf026`, 21,968 bytes, 412 lines),
which stays on disk byte-unchanged. **Everything in rev 6 stands except where this document says
otherwise.** Rev 6's Findings 27–32 — the node-child encoding, one-item termination, the
`resolved` token, the absent/`null` equivalence, the diagnostic-precedence scoping, and the
`retrieved_at` canonical form — are all unchanged and are not restated here. Rev 5's Findings
24–26, rev 4's Findings 15–23, the four-member preimage, the `ao-evidence-leaf-v2` prefix, and
the four-term sort key likewise stand.

**Base:** `drafts/evidence-pinning-02-review-draft.md`, sha256
`9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096`, 14,469 bytes, 289 lines.

**New filename per `semantics_change_new_filename.md`.** This revision adds a required member to
every `MALFORMED` vector and renames two vector identifiers, both of which change what a
conformant implementation is checked against. Rev 6 and rev 7 are not interchangeable.

---

## Why this revision exists

On 2026-09-09 Michael Msebenzi ran the rev 6 set. **22 of 22 root values agreed, 29 of 29
relations held, zero divergences.** His roots entered a signed commit at 11:44Z; the first read
of any computed member of this side's fixture was 11:45Z; the generator and the cross-check were
never opened. Commits `e9b98db` and `e2cd882`, suite 646–662, verify history 83 of 83.

Rev 6's E-3 airlock fix worked as intended: no vector carried `correct_root` inside `input`, so
no root-side disclosure was needed this run.

He also filed three findings against the set. Two are corrections to this side's work and one is
a structural defect in the airlock. All three are taken, and the third is generalized past what
he claimed, because on inspection the leak he found is wider than the field he found it in.

**One limit he stated himself, and it is load-bearing for how -02 describes this run.** His rev 6
work extended his 2026-09-07 implementation rather than rebuilding cold. It could confirm that
rev 6's sentences match his reading of them. It could not have found a *second* uncompelled
choice, because he made the first one. **-02 must describe this as confirmed-by-extension and
must not describe it as an independent second implementation.** The two are different claims and
the surviving-claim set depends on not blurring them.

---

## E-4 — the group arithmetic is wrong, and the error is a double subtraction

Rev 6 l.319 and `evidence-pinning-fixture-README-rev6.md` l.116 both give **Remaining: 5**.

**It is 6.** Verified independently by recounting the emitted set: 12 root-bearing (vectors
carrying a `computed` member), 12 `MALFORMED`, 6 in neither group, and exactly one vector —
`evi-root-mismatch-rejects` — in both of the first two.

The six are the same six under rev 5 and under rev 6, and none of them left the group:
`evi-empty-root-null`, `evi-absent-unknown`, `evi-partial-resolves-unknown`,
`evi-declared-partial-is-not-invalid`, `evi-content-mismatch-unknown`,
`evi-content-not-held-unknown`.

**The error was subtracting the overlap from the wrong group.** Rev 6 correctly identified that
the groups stopped partitioning the set, then reduced *Remaining* from 6 to 5 so that
`12 + 12 + 5` would reach 29. But the overlap is between root-bearing and `MALFORMED`; it does
not touch Remaining at all. The correct arithmetic is:

> **12 + 12 + 6 − 1 = 29**, or **11 + 12 + 6 = 29** counting root-bearing by designation alone.

Rev 6 l.328–329 and README l.121–122 already instruct the next run not to present the groups as
a partition. Reducing Remaining to 5 is that exact mistake, committed in the table those
sentences warn about. No root value is affected.

**Correct rev 6 l.315–319 and README l.111–116 to read:**

> | | rev 5 | rev 6 |
> |---|---|---|
> | Root-bearing vectors | 10 | **12** |
> | Root values carried | 19 | **22** |
> | `MALFORMED` | 12 | 12 |
> | Remaining (`ADDITIVE`, `COMPLETENESS`, `UNKNOWN`, `EMPTY`) | 6 | 6 |
> | Overlap (`MALFORMED` **and** root-bearing) | 0 | **1** |
>
> 12 + 12 + 6 − 1 = 29.

---

## Finding 33 — `MALFORMED` expectations are prose, so the set cannot check *why* a halt occurred

This is the finding that matters in this revision, and it is the cause of which rev 6's Finding
31 was only a symptom.

Every `MALFORMED` vector's `expect` member is the string `"halt, malformed"`. One carries a
prose qualifier about the diagnostic. **No vector names the condition that is supposed to fire.**

**The consequence.** The twelve `MALFORMED` vectors verify *that* an implementation halts. They
cannot verify that it halted *for the stated reason*. Two implementations can pass all twelve
while rejecting each input on entirely different grounds, and nothing in the set detects it. An
implementation with one over-broad predicate that rejects any set containing a `null` would pass
several of them for the wrong reason.

**Why this produced Finding 31.** Michael could not answer, from his validator, whether any
vector injects two coexisting conditions, because the validator returns on first match. He
resolved it by writing the fifteen malformed predicates out a second time and evaluating every
one over the same inputs — the right instrument, and the only one available, because *the fixture
gave him nothing to compare a condition against.* Rev 6 then scoped the coexistence rule out on
the grounds that it is never reached. That disposition is correct for rev 6's set. It is correct
only because the set cannot express the thing the rule is about.

**Amendment — add a required `condition` member to every `MALFORMED` vector.** The value is a
stable identifier naming the single condition the input injects. An implementation reports which
condition it halted on; conformance requires the reported condition to equal the vector's
`condition`, not merely that a halt occurred.

The twelve identifiers, one per vector, each derived from the rule the vector already targets:

| Vector | `condition` |
|---|---|
| `evi-set-retrieved-at-not-earliest-rejects` | `set_retrieved_at_not_first_in_canonical_order` |
| `evi-content-kind-absent-when-pinned-rejects` | `content_kind_absent_when_pinned` |
| `evi-resource-sha256-with-full-resource-rejects` | `snippet_digest_present_for_full_resource` |
| `evi-empty-set-rejects` | `pinned_set_empty` |
| `evi-duplicate-bound-tuple-rejects` | `duplicate_bound_tuple` |
| `evi-unpinned-reason-outside-domain-rejects` | `unpinned_reason_outside_domain` |
| `evi-unpinned-without-reason-rejects` | `unpinned_without_reason` |
| `evi-source-count-mismatch-rejects` | `source_count_disagrees_with_sources` |
| `evi-count-inconsistency-rejects` | `pinned_count_disagrees_with_pinned_entries` |
| `evi-root-with-zero-pinned-rejects` | `root_present_with_zero_pinned` |
| `evi-nonzero-pinned-null-root-rejects` | `root_null_with_pinned_entries` |
| `evi-root-mismatch-rejects` | `root_not_recomputable_from_sources` |
| `evi-retrieved-at-noncanonical-rejects` (new, below) | `retrieved_at_not_canonical_form` |

**What this makes possible for the first time.** Once every vector names its condition, the set
of named conditions can be diffed mechanically against the enumeration of malformed conditions in
the specification text. Michael's count of that enumeration is fifteen. Thirteen conditions are
now named by vectors, each injecting exactly one. **The remaining conditions in the enumeration
have no vector**, and identifying precisely which ones is now a diff rather than an audit. That
diff is not performed in this revision and is the first item for rev 8.

**Note on rev 6's Finding 31.** Its scoping-out stands as written for diagnostic *naming*, which
remains free. What changes is that conformance now depends on the reported condition matching, so
a future set *can* carry a two-condition vector and state which must be reported. Rev 6's premise
— that every current `MALFORMED` vector injects exactly one condition — was checked by Michael
and holds; it is recorded in the `condition` members above rather than left to be re-derived.

---

## Finding 34 — the fixture states the answers it exists to check

Michael's third finding: `evi-node-raw-not-hex` names which branch the answer takes, and `id` is
on the permitted side of the extraction whitelist, so "a whitelist that lets a descriptive id
through lets the answer through with it."

**Taken, and the leak is wider than the identifier.** For that one vector the resolution is
stated in four separate places:

1. `id` — `evi-node-raw-not-hex`.
2. `computed` key names — `normative_raw_children_root`, `non_normative_hex_children_root`.
3. `expect` prose — "an implementation encoding node children as hex characters computes
   `non_normative_hex_children_root` and fails this vector."
4. `header.node_child_encoding` — "raw-octets: in the interior node, left and right are the 32
   raw octets of the child digests, not their hexadecimal form."

`evi-leaf-hex-not-raw` has the identical construction for the leaf preimage, where the resolution
runs the *opposite* way.

**So the airlock cannot be repaired by moving fields between the permitted and excluded sides.**
The disclosure is distributed across every human-readable member. Any one of the four is
sufficient to hand an implementer the answer.

**The principle, stated so it constrains future vectors rather than patching these two:**

> **A conformance vector verifies a choice. The specification states it.** A vector's identifier,
> key names, and expectation text name the *dimension* under test and the *relation* that must
> hold. They must not name the resolution. An implementation that can pass a vector without
> having read the specification has been handed the answer, and the vector has measured nothing.

**Amendments:**

- `evi-node-raw-not-hex` → **`evi-node-child-encoding`**
- `evi-leaf-hex-not-raw` → **`evi-leaf-member-encoding`**
- In both, `computed` keys become **`normative_root`** and **`counter_construction_root`**, with
  **`differ`** unchanged. The reader learns that the two must differ and which one their
  implementation must match — not which encoding produces it.
- `expect` becomes: `evidence_root MUST equal normative_root and MUST NOT equal
  counter_construction_root. The encoding is stated normatively in the specification and is
  deliberately not restated here.`
- `header.node_child_encoding` and `header.leaf_member_encoding` cite the governing finding and
  base lines instead of restating the rule.
- The generator and cross-check **assert** that no vector identifier or `computed` key contains a
  resolution token (`raw`, `hex`, `normative_raw`, `not-hex`, and the like). A future vector that
  names its answer fails the build rather than shipping.

**What this does not do.** It does not retroactively restore the airlock for the runs already
completed. Michael saw the identifier at extraction on the rev 6 run and recorded it; the
Finding 27 resolution was additionally disclosed in prose, deliberately, in correspondence with
Pablo Play so that his independence signal would be honest rather than accidental. **The Finding
27 branch is therefore not available for independent corroboration by either of them.** This
amendment protects the third implementer onward, and it protects every future dimension from the
same construction.

---

## Vectors for three rules rev 6 states and its own set does not exercise

Michael's first finding lists four rules rev 6 states that no vector reaches. Three are closed
here with vectors. The fourth is Finding 31's coexistence rule, which Finding 33 above converts
from unreachable to expressible without adding a vector for it in this revision.

### 33a — `resolved` is never expected by any vector

Rev 6 Finding 29 names `resolved` as the affirmative step resolution, the pair to `unknown`. **No
vector in the 29 expects an affirmative resolution** — verified by inspection: fifteen expect a
halt, four expect `unknown`, and none expect `resolved`. This is the only rule in rev 6 that
changes an output value for a *conformant* input, and the set that shipped with it cannot tell
whether an implementation emits the right token or an arbitrary one.

**New vector `evi-step-resolves-affirmatively`**, designation `RESOLUTION`: a fully pinned
two-item set with all content held and matching, and a recomputable root. Expectation: the step
resolves `resolved`, not `unknown` and not a halt.

### 33b — the `absent` limb of the absent-or-`null` equivalence

Rev 6 Finding 30 makes an absent member and an explicit `null` equivalent on unpinned entries.
**All seven unpinned entries in the set carry explicit `null` and none omits the key** — verified
by walking the emitted fixture. The equivalence is half exercised, and the failure it guards
against is an implementation that requires the key to be present-and-`null` and rejects absence.

**New vector `evi-unpinned-members-absent-accepted`**, designation `ADDITIVE`: an unpinned entry
with `snippet_sha256` and `content_kind` **omitted entirely**, alongside one pinned entry.
Expectation: accepted, treated identically to the explicit-`null` form.

**This vector carries no new root value and is not root-bearing.** Only pinned entries form
leaves, so the root is a function of the pinned entry alone and would be equal to the
explicit-`null` counterpart by construction. Asserting that equality would be an assertion about
this generator rather than about the specification. The vector's content is acceptance, and it is
designated accordingly rather than counted as a root.

### 33c — the `retrieved_at` canonical-form rejection fires on no input

Rev 6 Finding 32 adds the only input-validation rejection in that revision: `retrieved_at` MUST
be RFC 3339 UTC with `Z` and **exactly three** fractional-second digits, and an implementation
MUST reject anything else. **Both `retrieved_at` literals in the set are already canonical**
(`2026-09-01T12:00:00.000Z`, `2026-09-02T12:00:00.000Z`), so the halt fires on no vector.

**New vector `evi-retrieved-at-noncanonical-rejects`**, designation `MALFORMED`, condition
`retrieved_at_not_canonical_form`: a pinned entry whose `retrieved_at` is
`2026-09-01T12:00:00Z` — same instant, zero fractional digits. Expectation: halt, with the
reported condition equal to `retrieved_at_not_canonical_form`.

> The zero-digit spelling is chosen deliberately as the counter-example, because it is the form a
> reader is most likely to assume is canonical. A checker written against "RFC 3339 with `Z`"
> without reading the three-digit clause accepts it.

---

## Set size after this revision

| | rev 6 | rev 7 |
|---|---|---|
| Total vectors | 29 | **32** |
| Root-bearing vectors | 12 | **13** |
| Root values carried | 22 | **23** |
| `MALFORMED` | 12 | **13** |
| Remaining | 6 | **7** |
| Overlap (`MALFORMED` and root-bearing) | 1 | 1 |

13 + 13 + 7 − 1 = 32. The overlap is still `evi-root-mismatch-rejects` alone.
`evi-step-resolves-affirmatively` is root-bearing and adds one root value.
`evi-retrieved-at-noncanonical-rejects` is `MALFORMED` and carries no root.
`evi-unpinned-members-absent-accepted` is in neither group, per 33b.

---

## Findings ledger — 33–34

| # | Finding | Source | Disposition |
|---|---|---|---|
| E-4 | Remaining counted as 5; overlap subtracted from the wrong group | `headlessoracle` | **Corrected** — 12 + 12 + 6 − 1 = 29. No root affected. |
| 33 | `MALFORMED` expectations are prose; the set cannot check why a halt occurred | derived from `headlessoracle`'s Finding 31 method | **Normative amendment** — required `condition` member on every `MALFORMED` vector. |
| 33a | `resolved` expected by no vector | `headlessoracle` | **New vector** `evi-step-resolves-affirmatively`. |
| 33b | `absent` limb of the absent-or-`null` equivalence unexercised | `headlessoracle` | **New vector** `evi-unpinned-members-absent-accepted`, acceptance only. |
| 33c | `retrieved_at` canonical-form rejection fires on no input | `headlessoracle` | **New vector** `evi-retrieved-at-noncanonical-rejects`. |
| 34 | Vector identifiers, key names, expectation text, and header restate the resolutions they test | `headlessoracle`, generalized | **Normative amendment** — two renames, key renames, header citations, and a build-time assertion. |

**Attribution.** Findings 33a, 33b, 33c, E-4, and the identifier half of Finding 34 are Michael
Msebenzi's, reported against the rev 6 set on 2026-09-09. Finding 33's statement of cause, and
the generalization of Finding 34 past the identifier to the key names, expectation text, and
header, are this side's, derived from his report. He is the source of both the arithmetic error
and the airlock defect in this side's own package, unprompted, in successive runs.

## What remains open for rev 8

1. **The condition-enumeration diff.** Now mechanically possible: diff the thirteen named
   `condition` values against the malformed-condition enumeration in the specification text, and
   name the conditions that have no vector.
2. **A cold build.** Every run of this set to date has been by a party who had already
   implemented an earlier revision of it. Pablo Play's build against rev 6 is in progress on his
   own clock. Until a cold build lands, no revision of this section has had an independent
   implementation in the sense the README defines, and -02 must not claim one.
