# Evidence pinning — amendments rev 6 for `draft-krausz-verification-state-02`

**Status: DRAFT amendments for review. Not filed. Not implemented.**

**Replaces** `evidence-pinning-02-amendments-rev5-2026-09-06.md` (sha256
`1f901fd7d56fcfe9f858446e5b685b540b5904d6abcfb4b2509e1eb675aa1e51`, 14,631 bytes, 256 lines),
which stays on disk byte-unchanged. **Everything in rev 5 stands except where this document
says otherwise.** Rev 5's Findings 24–26, its distinctness prohibition on the four bound
members, the out-of-domain literal, the possession-collapse placement in §5, and the
filing-day-tip citation rule are all unchanged and are not restated here. Rev 4's Findings
15–23, the four-member preimage, the `ao-evidence-leaf-v2` prefix, the four-term sort key, and
Finding 20's empty-set prohibition likewise stand.

**Base:** `drafts/evidence-pinning-02-review-draft.md`, sha256
`9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096`, 14,469 bytes, 289 lines.
Re-derived from `TKCollective/agentoracle-receipt-spec` at HEAD
`ac33ad1dd660ea8473123ab8a3371934255926e9` at build time and compared byte-for-byte against the
local copy. Identical.

**New filename per `semantics_change_new_filename.md`.** This revision states a construction
rule the text did not previously state (Finding 27), which changes what a conformant
implementation must do. Rev 5 and rev 6 are not interchangeable.

---

## Why this revision exists

On 2026-09-07 Michael Msebenzi completed an independent implementation of this section, built
from the review draft and the amendment texts alone at `agentoracle-receipt-spec@ac33ad1`,
with his roots committed to `receipt-verify` before any of this side's generator or cross-check
files were opened. Commits `80ca6a6` and `5ffb455`. The run agreed on all 28 vectors.

**It also found the gap this revision closes.** From his report:

> The interior node's children have no stated encoding. Base l.121 gives
> `node = SHA-256("ao-evidence-node-v1" || 0x00 || left || 0x00 || right)`, and no sentence in
> the five files says whether `left` and `right` enter as 32 raw octets or as 64 hex
> characters. Rev 2 Finding 1 settles that question for `snippet_sha256` and scopes itself, in
> its own words, to the leaf preimage. We took raw octets [...] Your generator took the same
> branch, or the multi-leaf roots would not match. Nothing in the text compelled it.

Pote confirmed the class independently:

> preimage encoding raw-vs-hex gives identical roots on single-item vectors and diverges on
> multi-item, so two implementations both picking raw octets agree by luck and the fixtures are
> blind to it — no vector distinguishes the two.

**What that means precisely, and what it does not mean.** The agreement between the two
implementations is a completed measurement and its strength is fixed. So is its limitation:
the set as run could not have detected a different choice. Neither is changed by this revision.
What this revision changes is what the *next* independent implementation can establish — with
Finding 27 stated and its vector present, a third implementer either takes raw octets or
visibly fails a vector.

---

## Finding 27 — the interior node's children have no stated encoding

**Severity: normative gap. This is the one choice in the whole construction that changes
bytes and that no sentence pins.**

Base l.119–122 reads:

> **Interior node.**
>
> ```
> node = SHA-256( "ao-evidence-node-v1" || 0x00 || left || 0x00 || right )
> ```

Base l.113–116 states, for the leaf, that `url` and `snippet_sha256` are "their UTF-8 bytes."
Rev 2 Finding 1 sharpens that to the 64 lowercase hexadecimal characters encoded UTF-8 for
`snippet_sha256`, and scopes itself explicitly to the leaf preimage. Rev 4's 15a widens the
leaf preimage to four members and keeps that scoping.

**Nothing in any of the five texts states the encoding of `left` and `right`.** A reader may
take them as the 32 raw octets that `SHA-256` outputs, or as the 64 lowercase hexadecimal
characters those octets print as. Both readings are defensible from the text as it stands.

The consequence is exact:

- On a pinned set of **one** item, the root is the leaf and no interior node is formed.
  Both readings agree.
- On a pinned set of **two or more**, at least one interior node is formed and the two
  readings produce different roots on every such set.
- Every **relational** expectation in the rev 5 fixture set — order independence, tie-break
  ordering, "these two roots must differ", odd promotion — holds under both readings, because
  each compares two roots computed under the same branch.

So an implementation that chose hex would pass the entire rev 5 fixture set.

### The amendment

**Amend base l.119–122 to read**, in Michael's words:

> **Interior node.**
>
> ```
> node = SHA-256( "ao-evidence-node-v1" || 0x00 || left || 0x00 || right )
> ```
>
> In the interior node, `left` and `right` are the 32 raw octets of the child digests, not
> their hexadecimal form. This differs from the leaf preimage deliberately: a leaf's members
> are values carried in the receipt as strings and enter as their UTF-8 bytes, whereas a
> node's children are outputs of this function and enter as the octets the function produced.

### The 0x00 delimiter clause, and what rev 4's argument does not cover

Rev 4 argues at base l.106–109 that the `0x00` delimiter makes the leaf preimage unambiguous,
which holds because no leaf member may contain a `0x00` byte — `url` is a URL, and the other
three members are constrained strings.

**That argument scopes to leaf members and does not extend to the node.** Under raw octets a
child digest may contain `0x00` at any position; roughly one digest in eight does. The node
preimage is nevertheless unambiguous, but for a different reason: **both children are
fixed-length 32-octet values, so their boundaries are determined by position rather than by
the delimiter.** The `0x00` separators in the node preimage are retained for consistency with
the leaf form and for domain hygiene; they are not what makes the preimage parseable.

**Add after the amended interior-node paragraph:**

> The `0x00` separators in the node preimage are retained for consistency with the leaf form.
> Unlike the leaf, they are not what makes this preimage unambiguous: both children are
> fixed-length 32-octet digests and their boundaries follow from position. A child digest may
> itself contain `0x00` octets, and this is harmless. The leaf preimage's no-embedded-`0x00`
> property, relied on at base l.106–109, is a property of leaf members and is not claimed for
> node children.

### Conformance vector

A new vector, `evi-node-raw-not-hex`, carries a two-item pinned set, the concrete
`evidence_root` under raw-octet children, and the counter-construction root under hex
children, with the requirement that the two differ. It is the node-level analogue of the
existing `evi-leaf-hex-not-raw`, which covers only the leaf. **An implementation that chose
hex children fails this vector alone, on its concrete root, with no relational comparison
needed.**

---

## Finding 28 — termination is never stated

Base l.124–128 states the odd-node rule: the final entry of an odd level is promoted unchanged
and MUST NOT be duplicated and paired with itself. That governs an odd level, not the
one-element set.

**A pinned set of exactly one item is never addressed.** The construction as written implies
the root is that item's leaf, because there is no pair to combine and the level is already of
length one. But `node(leaf, leaf)` on a single item also satisfies every sentence in the
section — nothing forbids it, and the odd-node prohibition reads as a rule about levels with a
trailing element rather than about a level of length one.

The two readings disagree on every one-item vector, of which the rev 5 set has several.

**Add after the odd-node paragraph:**

> **Termination.** When the pinned set contains exactly one item, `evidence_root` is that
> item's leaf. No interior node is formed. Applying the node function to a single leaf paired
> with itself is forbidden, for the same second-preimage reason the odd-node rule gives.

---

## Finding 29 — the affirmative step-resolution token has no name

§4.3 defines `unknown` as a step resolution and states the conditions under which a step
resolves to it. **No token is defined for the affirmative case.** An implementation cannot
switch on a value the specification does not name, and the fixture set's expectations for
affirmative resolution are stated in prose ("step resolves unknown" for the negative case,
nothing for the positive).

**Amend §4.3 to name the pair:**

> A step resolves to exactly one of two values: `resolved`, when the step's evidence
> requirements are met, or `unknown`, under the conditions this section states. An
> implementation MUST emit one of these two tokens and MUST NOT emit any other value for a
> step's resolution.

`resolved` is chosen as the pair to `unknown` because it is the word the section's own
vector identifiers already use (`evi-partial-resolves-unknown`).

---

## Finding 30 — `content_kind` on unpinned entries: absent or `null`

Rev 4 Finding 21 states that `content_kind` is **absent** on an unpinned entry, since there is
no retrieved content whose kind could be described. The rev 5 fixture set writes
`content_kind: null` on all seven unpinned entries.

Michael read `null` as equivalent to absent, and recorded the reading rather than halting,
because the stricter reading halts five vectors for a reason those vectors do not target. That
reading was his and not the text's, and the text should say which is meant.

**Amend §4.1.1:**

> On an unpinned entry, `content_kind` MUST be absent or `null`; the two are equivalent and
> both mean no retrieved content is described. An implementation MUST NOT treat a `null`
> `content_kind` on an unpinned entry as a malformation. On a pinned entry, `content_kind`
> MUST be present and MUST be one of the defined values.

The fixture set is left as it stands, writing `null`, and this amendment makes that
conformant rather than tolerated.

---

## Finding 31 — which diagnostic fires when two malformations coexist

Rev 4's 18b and 18c fix the diagnostic precedence for two specific coexisting malformations.
For the other eleven malformation checks the precedence is open, and every vector in the set
injects exactly one condition, so the set never exercises a coexistence.

Two readers can differ on a receipt that violates two rules at once, and both can claim
conformance.

**Add to §4.3:**

> When a receipt violates more than one condition of this section, an implementation MUST halt
> and MAY name any one of the violated conditions in its diagnostic, except where a precedence
> is stated explicitly (18b, 18c). Conformance is determined by the halt, not by which
> condition is named. A conformance vector that injects more than one condition MUST state
> which diagnostics are acceptable.

This closes the question by declaring it out of scope for conformance rather than by
enumerating a precedence for every pair, which would be eleven rules to buy nothing: the
halt is the behaviour that matters and every reading halts.

---

## Finding 32 — `retrieved_at` ordering is bytewise, and that has a consequence

Base l.129–133 states that canonical order compares bytewise over UTF-8, extended by rev 4's
15c and rev 5's 24c to four terms including `retrieved_at`. Rev 5's Finding 12 refers to the
"earliest" `retrieved_at`, which reads temporally.

**Bytewise and temporal orderings differ.** `2026-09-01T12:00:00Z`,
`2026-09-01T12:00:00.000Z`, and `2026-09-01T12:00:00+00:00` are the same instant and sort
differently bytewise. The rev 5 set carries a single `retrieved_at` literal across all 28
vectors, so it never exercises the difference.

**The bytewise rule stands** — it is what makes the root computable without a date library —
and Finding 12's wording is corrected to match it.

**Amend rev 5's Finding 12 wording:** replace "earliest `retrieved_at`" with "first
`retrieved_at` in the canonical bytewise order." **And add to §4.1.1:**

> `retrieved_at` MUST be an RFC 3339 timestamp in UTC with the `Z` designator and exactly
> three fractional-second digits. This canonical form is required because the sort at
> §4.1.2 is bytewise: two spellings of one instant would otherwise order differently and
> produce different roots for the same evidence. An implementation MUST reject a
> `retrieved_at` that is not in this form.

This is the only amendment in this revision that adds a rejection condition to input
validation. It is stated as a MUST because the alternative — a bytewise sort over
uncanonicalized timestamps — makes the root a function of formatting choices.

---

## Errata — three corrections carried in this revision

These are not findings. They are stale values corrected at their source.

### E-1 — rev 4 l.402 vector count

Rev 4's section head at l.402 reads **"Retained unchanged — nine vectors"** over a list of
eleven, with two further vectors named as unchanged in the following paragraph. **Thirteen is
the correct count**, and the fixture README's "13 retained from rev 2" reconciles to 28
correctly against it.

**Rev 4 is not edited.** It stays on disk byte-unchanged at sha256
`060fc52c067b5d7da5a57d3ea6ef32e05aa0417bc4b1abd9fdf0f9f9faed731c`, per supersede-never-edit: a
reader holding rev 4 must be able to see what it said and what corrected it. The correction is
recorded here, and any citation of that list takes its count from this entry rather than from
rev 4's head.

### E-2 — fixture README reference digest

The README's Reproduce section at l.74 gives the fixture JSON's sha256 as
`fe8567bd734602838c0f70bdc0741e506ff5476207bc641ff77ba3a5ea68e5cc`. That is the file at
`ac33ad1^`. At `ac33ad1` the file hashes to
`5d499bd01f44bd6e0f12b3617c7f104a214555b57a6c80280f5ceb358409b587`; a header-only change after
the digest was written moved the hash. **No root was affected.** The consequence is that the
bundle could not verify itself through its own Reproduce section. Corrected, and the rev 6
README carries the rev 6 fixture digest.

### E-3 — the airlock leak in `evi-root-mismatch-rejects`

The vector carries `correct_root` inside its `input` member. Michael's protocol treats `input`
as the permitted side of the airlock, so one concrete normative root was visible to him before
his own roots were fixed. **He disclosed it: noticed at extraction, recorded, not consulted,
and his independent recomputation produced the same value.** The disclosure is complete and the
run's independence for the other 27 vectors is unaffected.

The fix is structural rather than procedural. `correct_root` moves from `input` to `computed`,
where the airlock already excludes it. **After this change no future run needs to make the
same disclosure**, because no normative root sits on the permitted side.

---

## Vector changelog — delta from rev 5

| Vector | Change | Finding |
|---|---|---|
| `evi-node-raw-not-hex` | **NEW.** Two-item pinned set, concrete root under raw-octet children, counter-construction root under hex children, the two MUST differ. | 27 |
| `evi-root-mismatch-rejects` | `correct_root` moves from `input` to `computed`. Input bytes otherwise unchanged. | E-3 |

**Count: 28 → 29.** Verified: 27 of the 28 shared vectors are byte-identical to rev 5, and the
only one that differs is `evi-root-mismatch-rejects`, whose `correct_root` value is unchanged
and has only moved between members. **No root value in the set changes.** The new vector's
normative root equals the value rev 5 already computed for the same two-entry set, confirming
that Finding 27 pins the branch this side had already taken rather than altering it.

### The category arithmetic changes, and the next run's line must use the new numbers

Michael's record line counts the rev 5 set as 19 root values on 10 vectors, 12 malformed, 6
resolution. **Those numbers are correct for rev 5 and wrong for rev 6.** Two things moved them:

| | rev 5 | rev 6 |
|---|---|---|
| Root-bearing vectors | 10 | **12** |
| Root values | 19 | **22** |
| `MALFORMED` | 12 | 12 |
| Remaining | 6 | **5** |

The new vector adds one root-bearing vector carrying two values. The airlock fix makes
`evi-root-mismatch-rejects` root-bearing for the first time, carrying one — **and the
categories now overlap**, because that vector is both `MALFORMED` and root-bearing. Under rev 5
the three groups partitioned the set; under rev 6 they do not.

That overlap is a gain, not an accounting nuisance: moving `correct_root` to the excluded side
of the airlock converts a leaked hint into a real comparison point, so a future run has one
more normative root to agree or disagree on. But **any line written about a rev 6 run must state
the overlap** rather than present 12 + 12 + 5 as a partition of 29, which it is not.

**Cross-language check on the rev 6 set:** 22 of 22 root values recomputed and matched — 20
under raw-octet children, 1 under the hex-children counter-construction, 1 under the leaf-level
raw-digest counter-construction. The rev 5 checker skipped that last one, leaving a value the
fixture asserted that no implementation verified; the rev 6 checker covers it, and treats an
unrecognised root key as a failure rather than a skip.

---

## Findings ledger — 27–32

| # | Finding | Disposition |
|---|---|---|
| 27 | Interior node children have no stated encoding | **Normative amendment** — raw octets, plus the 0x00 scoping clause. New vector. |
| 28 | Termination for a one-item pinned set is never stated | **Normative amendment** — root is the leaf; self-pairing forbidden. |
| 29 | Affirmative step resolution has no token | **Normative amendment** — `resolved` named as the pair to `unknown`. |
| 30 | `content_kind` absent vs `null` on unpinned entries | **Normative amendment** — the two are equivalent; fixture stands as written. |
| 31 | Diagnostic precedence under coexisting malformations | **Scoped out** — halt is the conformance behaviour; naming is free except 18b/18c. |
| 32 | Bytewise vs temporal `retrieved_at` ordering | **Normative amendment** — bytewise stands; canonical form required. |

---

## Slipping, named rather than drifted

**The fixture input-shape unification is not in this revision.** Michael's report identifies it
as the largest independence limitation:

> the set has eleven distinct input shapes across 28 vectors, one of them prose
> (`"receipt_shape": "no evidence_set member present"`), so a consumer needs a hand-written
> branch per vector; ours did. One shape, with the variation in named members, would make the
> set runnable by something that was not told about it in advance.

This is correct and it is the right next piece of work. It is **deferred to rev 7** and named
here rather than left to drift, because unifying eleven shapes into one touches every vector's
input and every consumer's parser, and doing it in the same revision as Finding 27 would mean
the node-encoding fix waits on a mechanical refactor. Finding 27 is what an implementer needs
in order to not be wrong; the shape unification is what a runner needs in order to be
convenient.

**Two requirements it must meet when it lands**, both from the report:

1. One top-level input shape, with per-vector variation carried in named members rather than
   in the shape.
2. No prose-valued input members. `"receipt_shape": "no evidence_set member present"` becomes
   a structural representation a parser can act on.

---

## What this revision does not settle

- **`evidence_set_version` and the set-level `retrieved_at`.** Base l.68–76 marks both
  required; all nine `evidence_set` inputs in the fixture omit them. Michael scoped his step (a)
  to the internal consistency of what a set declares and checked requiredness nowhere, and
  recorded that as his reading. Either the fixture gains the required members or the
  requiredness claim narrows. **Open, and it is a fixture-versus-text disagreement rather than
  an ambiguity** — one of the two is simply wrong, and deciding which is a rev 7 item alongside
  the shape unification.
- **Whether any other construction choice is uncompelled.** Finding 27 was found by an
  implementer building cold. The only honest statement about the remainder is that no equivalent
  gap is currently known, which is not the same as none existing. A second cold build against
  rev 6 is the instrument that would find another.

---

## For the record — the independence run, in its bounded form

Reviewed by Michael against his own commits before use:

> Two implementations, one written from the review draft and the amendment texts alone at
> `agentoracle-receipt-spec@ac33ad1` by an author who never opened the generator or
> cross-check, agree on all 28 vectors: identical bytes on every root the file carries (19
> values on 10 vectors), the 12 malformed vectors halting on the condition each targets, the 6
> resolution vectors matching their stated expectation. Two limits belong on the record beside
> the agreement. Airlock disclosure: `evi-root-mismatch-rejects` carried `correct_root` inside
> `input`; noted at extraction, recorded, not consulted; the independent recomputation produced
> the same value. Independence limit: one choice the texts leave open, the encoding of a node's
> children, both implementations made the same way; the set as run could not have detected a
> different choice; rev 6 states it. Independence run: `receipt-verify` `80ca6a6` and `5ffb455`
> against `agentoracle-receipt-spec` `ac33ad1`.

The vector counts in that line are Michael's and verify against the fixture file: 10
root-bearing vectors carrying 19 root values, 12 `MALFORMED`, and 6 remaining across
`ADDITIVE`, `COMPLETENESS`, and `UNKNOWN`. 10 + 12 + 6 = 28.
