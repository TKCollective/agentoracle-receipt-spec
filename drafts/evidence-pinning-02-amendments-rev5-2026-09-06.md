# Evidence pinning — amendments rev 5 for `draft-krausz-verification-state-02`

**Status: DRAFT amendments for review. Not filed. Not implemented.**

**Replaces** `evidence-pinning-02-amendments-rev4-2026-09-06.md` (sha256
`060fc52c067b5d7da5a57d3ea6ef32e05aa0417bc4b1abd9fdf0f9f9faed731c`, 28,914 bytes, 463 lines),
which stays on disk byte-unchanged. **Everything in rev 4 stands except where this document
says otherwise.** Rev 4's Findings 15–23, its four-member preimage, the `ao-evidence-leaf-v2`
prefix, the four-term sort key, the (d) MUST, Finding 19's prohibition, Finding 20's empty-set
prohibition, and Q-a's closure by construction are all unchanged and are not restated here.

**Base:** `drafts/evidence-pinning-02-review-draft.md`, sha256
`9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096`, 14,469 bytes, 289 lines.
Re-derived from `TKCollective/agentoracle-receipt-spec` at HEAD
`49b7d039576b17e39dd707c9f223de5670c9be86` and compared byte-for-byte against the local copy.
Identical.

**New filename per `semantics_change_new_filename.md`.** This revision adds a normative
prohibition rev 4 did not carry (Finding 24) and changes a conformance vector's input from an
abstract description to a required literal (Finding 25). Rev 4 and rev 5 are not
interchangeable.

**Three changes, from two reviewers, none a reversal:**

| # | Source | Change |
|---|---|---|
| 24 | `headlessoracle`, 2026-09-06 15:02 | Exact-duplicate bound tuples produce identical leaves; the root moves with the count of a fact rather than the fact |
| 25 | `poteshniy`, 2026-09-06 14:07 | The out-of-domain vector must carry `content_not_retained` as its literal input |
| 26 | `poteshniy`, 2026-09-06 14:07 | The possession collapse must read as a stated boundary in §5, not as commentary |

Finding 22's citation instruction is also amended, per `headlessoracle` at 15:02.

---

## Finding 24 — identical leaves, and the root that counts a fact twice

**Raised by `headlessoracle` on the third sort key, which he confirmed:**

> Once `content_kind` is in the preimage, url and digest no longer identify a leaf, so two
> entries that differ only in `content_kind` are unordered without it and the root depends on
> which the issuer listed first. `content_kind` as the third key makes the order total, on one
> condition rev 4 should state: what a set does with two entries alike in url, digest and
> `content_kind`. Sorted, they become two identical leaves, and the root then moves with the
> count of a fact rather than the fact. Either forbidden, or collapsed to one leaf before the
> root.

**The finding is correct and rev 4 does not address it.** Rev 4's sort-key paragraph reads
"two entries compare equal on the key only if their leaves are identical, in which case their
order cannot affect the root." That sentence is true about **order** and silent about
**multiplicity**. Two identical leaves both enter the tree, so a set listing one evidence item
twice produces a different root from a set listing it once — and with odd-node promotion, a
structurally different tree. The root becomes a function of redundant listing rather than of
evidence content.

**Scope narrows under rev 4's fourth sort term.** His formulation names three members because
it was written against the three-key proposal; his own next sentence anticipates the
resolution — "either `retrieved_at` is the fourth key or the duplicate rule says one entry per
url, digest and `content_kind`." Rev 4 took the fourth key. So the case requiring a rule is
entries identical on **all four** bound members, and the fourth key already makes the
retrieved_at-differs case ordered and legal.

### 24a — the prohibition

> Two entries in `sources` MUST NOT be identical across the full set of members bound by the
> leaf preimage: `url`, `snippet_sha256`, `content_kind`, and `retrieved_at`. An
> `evidence_set` carrying two such entries is a malformed receipt; gate decision = halt.
>
> **The prohibition is on exact duplication of a bound tuple, not on repeated retrieval.** Two
> entries sharing `url`, `snippet_sha256`, and `content_kind` and differing in `retrieved_at`
> record the same content retrieved at two moments; both are legitimate, both produce distinct
> leaves, and the fourth sort term of §4.1.2 orders them. Two entries sharing `url` and
> `content_kind` and differing in `snippet_sha256` record content that changed between
> retrievals; both are legitimate and the second sort term orders them. What is forbidden is
> the same retrieval recorded twice, which is the only case that yields identical leaves.

### 24b — why prohibition rather than collapsing to one leaf

He offered both. Prohibition, for three reasons:

1. **Collapsing breaks the correspondence the verification protocol relies on.** §4.3 (a)
   checks `source_count` and `pinned_count` against `sources`; §4.3 (b) recomputes the root.
   A root computed over a de-duplicated projection of `sources` would have a leaf count that
   no longer equals `pinned_count`, so a third quantity would be needed to relate the checked
   counts to the rooted set. Prohibition adds no member and is checkable inside step (a).
2. **It matches Finding 20's own reasoning.** Where a state already has a legitimate
   representation, this document forbids the second rather than defining it. The same
   retrieval has one legitimate representation: one entry.
3. **It keeps inclusion proofs unambiguous in the detached increment**, which is the increment
   the root exists for. Two identical leaves admit a proof that cannot say which entry it
   proves. Collapsing hides that; prohibition removes it.

### 24c — amendment to rev 4's sort-key paragraph

Rev 4's final clause is replaced, because it treats the equal-on-key case as harmless:

> **Canonical order.** Leaves are sorted ascending by `url`; where two entries share a `url`,
> by `snippet_sha256`; where they share both, by `content_kind`; and where they share all
> three, by `retrieved_at`. All four comparisons are bytewise over the UTF-8 encoding of the
> member as carried in the entry. The sort key is exactly the set of members bound by the leaf
> preimage. **Two entries therefore compare equal on the key only if their leaves are
> identical, which §4.1.1 forbids** — so within a well-formed set the order is total and no
> two leaves are equal. Sorting makes the root independent of retrieval rank, so two verifiers
> who retrieved the same evidence in different orders compute the same root.

### 24d — amendment to §4.3 (a)

Append to the step (a) checks:

> ... and that no two entries in `sources` are identical across `url`, `snippet_sha256`,
> `content_kind`, and `retrieved_at`. Any inconsistency is a malformed receipt; gate decision
> = halt.

**Vector added:** `evi-duplicate-bound-tuple-rejects` — MALFORMED — two entries identical on
all four bound members — halt, malformed.

**The distinctness check is not self-enforcing**, unlike Finding 18c. A duplicated tuple
produces a computable root; it produces the *wrong* root, and nothing downstream detects it.
The explicit check in step (a) is the only thing that catches it, which is the reason it is a
MUST in the array rule rather than a note in §4.1.2.

---

## Finding 25 — the out-of-domain vector must carry the loophole literal

**`poteshniy`:**

> `content_not_retained` leaving the enum but staying as the literal in the rejecting vector's
> input is exactly right: dropping it from the domain doesn't drop it from the tests, and
> because it was the loophole, the vector proving it's rejected is the one test that must
> exist.

**Taken.** Rev 4 carries `evi-unpinned-reason-outside-domain-rejects` with its input described
as "reason value not in the §4.1.1 domain." An arbitrary out-of-domain value does not
distinguish *"the loophole value is rejected"* from *"some unrecognised value is rejected"* —
the vector passes either way, and the specific regression it exists to prevent goes
unexercised. This is
`a_check_that_cannot_distinguish_states_is_not_a_check.md` applied to a fixture input.

**Amended vector row:**

| id | designation | input | expect |
|---|---|---|---|
| `evi-unpinned-reason-outside-domain-rejects` | MALFORMED | `pinned: false` with `unpinned_reason: "content_not_retained"` — the literal value removed from the domain by rev 3 | halt, malformed |

The literal is **required**, not exemplary. A second vector carrying an arbitrary unrecognised
value MAY be added and does not substitute for this one: the rule under test is that the
retention branch is gone, and only the retention literal tests it.

---

## Finding 26 — the possession collapse belongs in §5

**`poteshniy`:**

> Noted on lines 103-105 — I'll confirm at line-check that it reads as a stated boundary in the
> limits section, not an oversight. The receipt collapsing "server declined" and "issuer chose
> not to request" into one declared state is the honest limit, and it should be visibly
> deliberate.

**Taken.** The collapse is currently stated in rev 3's *"Does not close"* commentary, which is
provenance prose rather than normative text, and rev 4 does not carry it into §5. A reader of
the filed draft would not find it in the limits section. Added as a fifth §5 bullet:

> - **Not why content was absent.** `no_content_returned` records that no content bytes
>   arrived. It does **not** distinguish a server that declined from an issuer that chose not
>   to request, and the receipt cannot be made to: both are the same fact about the issuer's
>   possession, and the difference lies in conduct the receipt does not observe. **This
>   collapse is deliberate.** §4.1.1's possession rule reaches only items for which bytes
>   actually arrived, so an issuer that never requested a source it should have requested is
>   outside what this format establishes. That limit is stated here rather than left to be
>   discovered.

§5 now carries five limits: not-unchanged, not-completeness-of-disclosure, not-the-time,
not-unbiased-selection, and not-why-content-was-absent.

---

## Finding 22 amended — the citation takes its count from the filing-day tip

**`headlessoracle`:**

> One note on the citation in 8: the count moves again this week, 67 at `46d3909` once it is
> pushed, so take the number from the tip on the day you file and say the commit.

**Taken, and the instruction is written into the text so it cannot go stale again.**
Re-derived at build time: the repository stands at **65 commits**, `dd21d5e` resolves with
committer date `2026-09-05T18:52:34Z`, and **`46d3909` does not resolve — it is not yet
pushed**, consistent with his "once it is pushed."

**Replaces rev 4's §8 verification sentence:**

> Verified against the registry and the repository, not taken from the message: the integrity
> string matches the published dist exactly, `0.1.2` is the `latest` tag, and every commit in
> the repository's history at the commit named below carries a verified signature. **The count
> and the commit MUST both be taken from the repository tip on the day this document is filed,
> and the commit MUST be named beside the count.** A count without its commit is unverifiable
> a week later. At the last verification for this revision the history stood at 59 of 59 at
> `6a94549` (4 September 2026) and at 65 at `dd21d5e` (5 September 2026); the repository has
> continued to advance. The published tarball was compared file-for-file against a fresh build
> of the tagged commit on a second machine and found identical — a check `0.1.1` could not
> pass, which is the reason this supersedes it.

---

## Vector changelog — delta from rev 4

**Added — one:** `evi-duplicate-bound-tuple-rejects` (Finding 24).

**Amended — one:** `evi-unpinned-reason-outside-domain-rejects`, input changed from an abstract
description to the required literal `content_not_retained` (Finding 25). Expectation unchanged.

**Unchanged — all others**, including rev 4's eight additions, the five relational expectations
that survive the widening, and `evi-duplicate-url-distinct-digest` as restated in rev 4. The
pair rule stands.

Rev 4's finding that **no published fixture is invalidated** is unaffected: `evi-duplicate-bound-tuple-rejects`
is a new malformed-input vector carrying no root value, and Finding 25 changes an input literal,
not an expectation.

## Findings ledger — 24–26

| # | Finding | Source | Disposition |
|---|---|---|---|
| 24 | Identical bound tuples yield identical leaves; root counts a fact twice | `headlessoracle` | **Taken by prohibition** — §4.1.1 distinctness rule, §4.3 (a) check, rev 4's sort-key clause amended, vector added |
| 25 | Out-of-domain vector must carry the `content_not_retained` literal | `poteshniy` | **Taken** — input required, not exemplary |
| 26 | Possession collapse must be a stated §5 limit | `poteshniy` | **Taken** — fifth §5 bullet |
| 22 | Citation count and commit | `headlessoracle` | **Amended** — filing-day tip, commit named beside count |

Findings 1–14 stand as filed in rev 2 (Finding 6 as amended by rev 3; Finding 3 as extended by
rev 4's 15a and 19). Findings 15–23 stand as filed in rev 4, with 15c amended by 24c and 22
amended above.

## Open questions

- **Q-a** — closed by construction (rev 4, Finding 21).
- **Q-b** — closed by rev 3.
- **Q-c** — closed for the leaf preimage by rev 4's 15b; the prefix is the version marker.
  Open only for members outside the preimage.

No new open questions. Both reviewers have now confirmed the preimage widening, the prefix
bump, and the sort key.

## What this revision does not settle

- **The fixture set, which still does not exist.** Rev 4's statement stands: this series
  specifies inputs and relational expectations and does not materialize concrete entries or
  compute roots. The set must be built under `ao-evidence-leaf-v2` with the four-term sort and
  the distinctness rule applied, then cross-checked before filing. The distinction rev 4 records
  is restated because it governs how the result may be described: agreement between two
  implementations **written by the same party** is a cross-language check that catches
  language-specific defects. It is **not** an independent implementation and MUST NOT be
  described as one.
- **The §5 cross-reference number** (rev 4, Finding 23), which depends on the filed draft's
  numbering. The named form is correct under either.
- **The filing-day count and commit** for §8, by construction — Finding 22 now requires them to
  be taken at filing rather than fixed here.
