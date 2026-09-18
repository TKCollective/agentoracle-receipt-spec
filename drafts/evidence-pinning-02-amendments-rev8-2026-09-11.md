# Evidence pinning — amendments rev 8 for `draft-krausz-verification-state-02`

**Status: DRAFT amendments for review. Not filed. Not implemented. HELD — not final.**

**Held deliberately.** Michael Msebenzi reported that the two scope questions ruled here are two of
**seven** all-versus-pinned scope choices he found in this text; he named one more (Finding 38
below) and holds five. This revision rules on the three he named and **reserves the remaining
five**, which are listed as open below with no ruling attached. Rev 8 is not final until they land.
Ruling all seven in one revision beats shipping rev 8 and finding a seventh scope choice next week.

**Replaces** `evidence-pinning-02-amendments-rev7-2026-09-09.md` (sha256
`6b13f6fc35d745c2642edcb52a2754f7cd43340ded3248b5d1ba70a431d6c037`, 17,732 bytes, 296 lines),
which stays on disk byte-unchanged. **Everything in rev 7 stands except where this document says
otherwise.** Rev 7's Finding 33 (the required `condition` member) and Finding 34 (a vector must not
name the resolution it tests) both stand; one build assertion shipped alongside Finding 33 is
withdrawn by Finding 39 below, and the finding itself is not weakened. Rev 6's Findings 27–32,
rev 5's Findings 24–26, rev 4's Findings 15–23, the four-member preimage, the `ao-evidence-leaf-v2`
prefix, and the four-term sort key all stand.

**Base:** `drafts/evidence-pinning-02-review-draft.md`, sha256
`9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096`, 14,469 bytes, 289 lines.

**Cut against** `main` at `3d0ec0e82229c1336340f0323d54904e5baf38b2`.

**New filename per `semantics_change_new_filename.md`.** This revision changes what a conformant
implementation is checked against: two rules move from a pinned-only reading to a
whole-of-`sources` reading, two condition identifiers are renamed, and four vectors are added that
a rev 7-conformant implementation reading those rules as pinned-only **passes today and fails
here**. Rev 7 and rev 8 are not interchangeable.

---

## Why this revision exists

**Both open questions are set-level rules expressed in §4.1.2's pinned-only vocabulary, and the fix
is to stop borrowing it.** §4.1.2 defines one thing — a sort over pinned leaves, because only
pinned entries have leaves — and it defines it well. Three later rules that range over `sources`
were then written in its words: "identical across the members bound by the leaf preimage,"
"first in canonical order," "the condition name `pinned_set_empty`." Each borrowed phrase silently
narrowed a set-level rule to the pinned subset, and each is repaired the same way: state the rule
in its own terms, over `sources`, and cite §4.1.2 only where a sort over leaves is actually meant.

This is not two independent judgement calls. It is one drafting habit with three instances, which
is why the ruling is the same in all three and why Finding 38's rename belongs in the same
revision rather than in a housekeeping pass.

**How the questions arrived.** Michael Msebenzi (`headlessoracle` in the findings ledgers) reported
on 2026-09-11 that his rev 7 implementation reads both rules over the full set, and gave the code:
`tools/evidence-root.ts` check 11 iterates `set.sources` with the four-member bound tuple, and for
an unpinned entry the key collapses so two unpinned entries sharing `url` and `retrieved_at` halt
with `duplicate_bound_tuple`. Pablo Play, reading the same text, took the pinned-only reading on
the entry-identity rule. **Both implementations pass all 32 rev 7 vectors.** Verified against the
rev 7 ledger: its only duplicate pair is two pinned entries, its only non-canonical `retrieved_at`
is on a pinned entry, and its one set-level `retrieved_at` comparison has both entries pinned.
Nothing in the shipped set distinguishes the readings, so the set agreed with both and neither
implementer was wrong to ship. That is a specification defect, not an implementation defect.

**What is not claimed for this run.** Michael's rev 7 result is confirmed-by-extension of his
earlier build, not an independent cold build, and rev 7's open item 2 stands unchanged: no
revision of this section has yet had an independent implementation in the sense the README defines,
and -02 must not claim one. The four counterfactual variant builds he reported are **not committed
at his tip** `4689b38` as of this writing; the ledger below records the finding, not the run.

---

## E-5 — a count in rev 7's own prose disagrees with the table beneath it

Rev 7 l.111 introduces the condition table as **"The twelve identifiers, one per vector."** The
table at l.113–127 has **thirteen** rows, and rev 7 l.131 says thirteen. The table and l.131 are
right; l.111 is wrong, and it is wrong in the same way rev 6's E-1 was: prose restating a count
that the artifact beneath it already determines.

**Correct rev 7 l.111 to read:**

> The thirteen identifiers, one per vector, each derived from the rule the vector already targets:

No condition, vector, or root value is affected. Rev 8's own group counts are not written by hand
at all — see the note under the set-size table.

## E-6 — Finding 12 is attributed to the wrong revision

Rev 6 l.229 says "Rev 5's Finding 12" and rev 6 l.240 says "Amend rev 5's Finding 12 wording."
**Finding 12 is rev 2's**, at rev 2 l.91–97, and the sentence rev 6 amends — "`retrieved_at` at set
level MUST equal the earliest per-item `retrieved_at` in `sources`" — is rev 2 l.95.

**Correct rev 6 l.229 and l.240 to attribute Finding 12 to rev 2 (l.91–97).** This matters beyond
tidiness: Finding 36 below restores the domain that rev 2 l.95 stated, and a reader chasing that
sentence through rev 5 does not find it.

## E-7 — the rev 7 README cannot verify its own bundle

Found while building rev 8, mechanically, and **this is rev 6's E-2 recurring in the same file.**
Three defects in `fixtures/evidence-pinning-fixture-README-rev7.md`:

1. **The quoted fixture digest is wrong.** l.220–221 gives
   `81cfd1bbb6e1f1a55e5ad8eebfeb78addef7465c14f6bd9f4dde8de7a224d9d9`. The shipped file hashes
   `a8679bdf5acb56ed7cd614086c5ea44438bcd6735b356e88c5e40172e8c696f1`, both on disk and at
   `3d0ec0e`. A reader following the Reproduce block gets a mismatch on a correct build.
2. **The Reproduce block runs the rev 6 files.** l.201–211 greps `rev6_sha256`, generates with
   `evidence-pinning-fixture-generator-rev6.py`, and cross-checks
   `evidence-pinning-fixtures-v2-rev6.json`, inside the rev 7 README.
3. **The expected figures are rev 6's.** l.213–218 state 22 roots checked (20 raw / 1 hex / 1 leaf)
   across 29 vectors. The rev 7 pair actually reports **23 roots checked (21 / 1 / 1) across 32
   vectors**, verified by running it.

Rev 7 is not edited. **The rev 8 README is generated-then-digested and its Reproduce block was
executed verbatim from a clean checkout before the digest was written**, which is the only remedy
that holds; E-2 was corrected once by re-writing a digest by hand and the defect returned two
revisions later.

---

## Finding 35 — the entry-identity rule ranges over every entry in `sources`

Rev 5's Finding 24a states the prohibition in the leaf preimage's terms: "identical across the full
set of members bound by the leaf preimage." Unpinned entries have no leaf, so the phrase invites
the reading that they are not covered — and 24c reinforces it by explaining that the sort key is
exactly the bound members.

**The full-set reading is the operative one, and the text already says so twice.** Rev 5 l.64 opens
24a with "Two entries **in `sources`**," and 24d's §4.3 (a) amendment at rev 5 l.109–110 repeats
"no two entries **in `sources`**." The pinned-only reading is an inference drawn from 24c's
supporting clause, not from either normative sentence. The repair is to restate the rule without
the preimage in it.

**Amendment — restate §4.3 (a)'s entry-identity check as:**

> No two entries in `sources` may record the same retrieval. Two entries record the same retrieval
> when they are identical in `url` and `retrieved_at` and, where both are pinned, also identical in
> `snippet_sha256` and `content_kind`. The rule ranges over every entry in `sources`, pinned and
> unpinned alike: `sources` carries one entry per item considered (base l.76), an issuer MUST NOT
> omit an item it could not pin (base l.100-102), and a second entry for one retrieval therefore
> overstates `source_count`. For an unpinned entry `snippet_sha256` is `null` and `content_kind` is
> absent (rev 4 l.294-296), so those members distinguish nothing and `url` with `retrieved_at`
> decides. An absent member is not equal to a present one, and two entries differing only in
> `unpinned_reason` are still one retrieval recorded twice. Malformed; gate decision = halt;
> reported condition `duplicate_bound_tuple`.

**Amendment to 24c (rev 5 l.100–101).** Replace "which §4.1.1 forbids" with **"which the
entry-identity rule of §4.3 (a) forbids,"** and add:

> This clause explains why the sort over pinned leaves is total. It does not scope the prohibition,
> which is stated in §4.3 (a) and ranges over all of `sources`.

The cross-reference was also wrong on its face: the prohibition has never been in §4.1.1.

**One consequence, stated because it is not obvious from the sentence.** "Where both are pinned"
means that a pinned entry and an unpinned entry sharing `url` and `retrieved_at` are also one
retrieval recorded twice: the qualifier is not met, so `url` with `retrieved_at` decides, and the
set halts. That is the fail-closed reading and it is intended — an issuer that pinned an item and
also reported it as unpinned has overstated `source_count` either way. **No vector in this revision
covers that pair**, and it is a candidate for the reserved findings below rather than something
rev 8 claims to have exercised.

**What does not change.** Rev 5's distinction between duplication and repeated retrieval stands:
two entries sharing `url`, `snippet_sha256`, and `content_kind` and differing in `retrieved_at`
are two legitimate retrievals of the same content, and both produce distinct leaves.

## Finding 36 — the set-level `retrieved_at` is the bytewise-least value in `sources`

Rev 2's Finding 12 (l.91–97) defined the set-level member over "the earliest per-item
`retrieved_at` **in `sources`**." Rev 6's Finding 32 corrected "earliest" to "first in canonical
order" — right about the basis, and it imported §4.1.2's pinned-only sort (base l.107, l.110) into
a comparison that has nothing to do with leaves. **Canonical order is a sort over pinned leaves.
The set-level member is a comparison over entries.** Using the former's name for the latter is what
narrowed the domain.

**Amendment — replace rev 6 l.240–241 with:**

> `retrieved_at` at set level MUST equal the bytewise-least `retrieved_at` among all entries in
> `sources`, comparing the UTF-8 bytes of the member as carried. The comparison ranges over every
> entry, pinned and unpinned alike. It is well-defined because `sources` is non-empty (rev 4
> l.273-276) and every entry carries the member (base l.91). A value that is not the bytewise-least
> such value is a malformed receipt; gate decision = halt; reported condition
> `set_retrieved_at_not_bytewise_least`.

This restores rev 2 l.95's domain and keeps rev 6's bytewise basis. Rev 6's reasoning for bytewise
comparison — that the root must be computable without a date library — is untouched, and so is the
canonical-form requirement that makes bytewise and temporal order coincide.

## Finding 37 — the `retrieved_at` form rule ranges over every entry, and it keeps its place

Rev 6's Finding 32 adds the canonical-form requirement to §4.1.1, which is the per-entry section
(base l.83–103). **The placement is right and stays.** What is missing is the words: the rule as
written at rev 6 l.243–247 says "`retrieved_at` MUST be an RFC 3339 timestamp…" without saying
which entries it ranges over, and an implementation that evaluates it inside the pinned branch
never sees an unpinned entry's value.

**Amendment — amend rev 6 l.243–247 to read "every entry in `sources`, pinned and unpinned
alike," and add:**

> The form rule is evaluated for every entry in `sources` before any branch on `pinned`. An
> unpinned entry omits `content_kind` and carries a `null` `snippet_sha256`, but it carries a
> `retrieved_at` like any other entry (base l.91), and the value is compared bytewise at set level.
>
> This rule does not run directly on the set-level `retrieved_at` at base l.71. That member is
> forced into canonical form transitively, by Finding 36's equality: it must equal a member of
> `sources`, and every member of `sources` is in canonical form.

**Why the transitivity is stated rather than left implicit.** Base l.71 is a required member and a
reader looking for its form rule finds none. Adding a second form rule there would create two
places to change; stating the transitivity leaves one.

## Finding 38 — two condition identifiers name a subset the trigger does not use

Michael's third instance of the same class, and it is in this side's own rev 7 package. A condition
identifier is now normative output (rev 7 Finding 33): an implementation reports it and conformance
depends on the reported value matching. **An identifier that misnames its trigger is therefore a
defect in the specification's output vocabulary, not a cosmetic issue.**

**`pinned_set_empty` → `evidence_set_names_no_sources`.** The trigger is an empty `sources` array
or a `source_count` of zero (rev 4 l.273–276, implemented at his `tools/evidence-root.ts` l.335 as
`sources.length === 0 || set.source_count === 0`). An empty *pinned* subset is **legal** — base
l.139–140 requires `evidence_root` to be `null` in exactly that case, and `evi-empty-root-null`
asserts it. The rev 7 name says the legal state is the malformed one. The new name is taken from
rev 4 l.281–282's own sentence: "The prohibition is on an evidence set that names no sources, never
on one that pins none."

**`set_retrieved_at_not_first_in_canonical_order` → `set_retrieved_at_not_bytewise_least`.**
Consequential on Finding 36: "canonical order" is §4.1.2's pinned-only sort, and the condition is
about a bytewise comparison over all of `sources`.

**Superseded identifiers are published, not dropped.** A run against rev 7 reported the old value,
and a reader comparing two runs must be able to map it:

| superseded identifier (rev 7) | identifier (rev 8) |
|---|---|
| `pinned_set_empty` | `evidence_set_names_no_sources` |
| `set_retrieved_at_not_first_in_canonical_order` | `set_retrieved_at_not_bytewise_least` |

The mapping ships in `header.superseded_conditions` of the fixture file, and the generator and
cross-check both **fail the build** if any vector names a superseded identifier. A future rename
adds a row; it never silently replaces a value.

## Finding 39 — condition identifiers are not one-per-vector, and rev 7's build asserted that they were

Not a scope choice and not reported by a reviewer: found while building rev 8's set, and recorded
because it changes a shipped build assertion.

Rev 7's Finding 33 requires that every `MALFORMED` vector name **exactly one** condition. Correct,
and unchanged. Alongside it, the rev 7 generator and cross-check also assert that **no two vectors
name the same condition** — which was true of the rev 7 set by accident of construction, one vector
having been written per condition, and was never stated as a rule.

Rev 8's set makes it false on purpose. Three of the four new vectors inject an already-vectored
condition on a **different entry class**: `duplicate_bound_tuple` on two unpinned entries,
`retrieved_at_not_canonical_form` on an unpinned entry, `set_retrieved_at_not_bytewise_least` with
the lesser value on an unpinned entry. Injecting the same condition from a different direction is
exactly how a scope rule gets covered, so the uniqueness assertion would fail a correct set.

**Amendment.** The uniqueness assertion is **withdrawn**. Every `MALFORMED` vector still names
exactly one condition; a condition may be named by more than one vector; and what replaces
uniqueness in the build is a check that no vector names a **superseded** identifier (Finding 38).
The condition-enumeration diff that rev 7 opens for rev 8 is unaffected — it compares the *set* of
named conditions against the enumeration in the specification text, and a set does not care how
many vectors reach each member.

---

## Vectors for the rules this revision scopes

Four vectors, and the point of each is that **the rev 7 set of 32 cannot fail on it.** Two
implementations that disagree about Findings 35 and 36 both pass rev 7; exactly one of them passes
rev 8.

The build proves that rather than asserting it. `assert_scope_discriminating` in the generator, and
the matching block in the cross-check, evaluate each new vector's own input under **both** the
whole-of-`sources` reading and the pinned-only reading and fail if the two agree. Run against a
generator holding the pinned-only reading, the build fails with five messages; against the shipped
set it passes. A vector that cannot fail on the defect it was added for is not evidence.

### `evi-duplicate-unpinned-entries-rejects` — `MALFORMED`, `duplicate_bound_tuple`

Two unpinned entries with the same `url` and the same `retrieved_at`, differing only in
`unpinned_reason` (`no_content_returned` and `provider_metadata_only`, both in the §4.1.1 domain).
`pinned_count` is zero, `evidence_root` is `null`, and the set-level `retrieved_at` is correct, so
the only condition injected is entry identity. Under the pinned-only reading the pair is invisible
and the set is accepted.

### `evi-unpinned-retrieved-at-noncanonical-rejects` — `MALFORMED`, `retrieved_at_not_canonical_form`

One pinned entry with a canonical `retrieved_at`, and one unpinned entry carrying
`2026-09-01T12:00:00Z` — the same instant as the pinned entry's value, zero fractional digits, the
spelling rev 7's Finding 33c already identified as the one a reader assumes is canonical.
`pinned_count` is 1, so the halt cannot be attributed to a zero-pinned set. The set-level
`retrieved_at` is the pinned entry's value, which is also the bytewise-least value in the set —
`.` sorts before `Z` — so Finding 36 is not co-injected.

### `evi-set-retrieved-at-equals-unpinned-value` — `SET SCOPE`, accepted

One pinned entry at `2026-09-01T12:00:00.000Z` and one unpinned entry at
`2026-08-31T12:00:00.000Z`; the set-level `retrieved_at` equals the latter. **Accepted**, and the
vector is root-bearing: the root over the pinned subset is a real normative value, and it is a
value an implementation with the wrong set-level domain still computes correctly — which is why
this vector turns on the set-level member and not on the root. Under the pinned-only reading the
set-level value is not the minimum and the receipt is rejected, so a correct implementation and an
incorrect one differ on an **accept**, not only on a halt.

### `evi-set-retrieved-at-above-unpinned-value-rejects` — `MALFORMED`, `set_retrieved_at_not_bytewise_least`

The same two entries, with the set-level `retrieved_at` set to the pinned entry's value instead.
Rejected under Finding 36 and accepted under the pinned-only reading. The pair is deliberate: one
limb fails an implementation that narrows the domain, the other fails one that widens it, and no
implementation passes both by mixing domains.

**Finding 34 compliance.** Neither set-level identifier names a resolution; both name the input
configuration (where the value sits, and how the set-level member compares to it), which is what a
reader needs to locate the vector. The two `expect` strings cite the governing rule and do not
restate it. The tension with Finding 33 is real and is resolved the same way rev 7 resolved it for
the existing thirteen: a `MALFORMED` vector must name its condition, and the condition identifier
necessarily encodes the rule it fires on — what Finding 34 forbids is naming which branch of an
**open** choice is normative. These choices are closed by this revision.

---

## Set size after this revision

| | rev 7 | rev 8 |
|---|---|---|
| Total vectors | 32 | **36** |
| Root-bearing vectors | 13 | **14** |
| Root values carried | 23 | **24** |
| `MALFORMED` | 13 | **16** |
| Remaining (`ADDITIVE`, `COMPLETENESS`, `UNKNOWN`, `EMPTY`) | 7 | 7 |
| Overlap (`MALFORMED` **and** root-bearing) | 1 | 1 |
| Distinct conditions named | 13 | 13 |

14 + 16 + 7 − 1 = 36. The overlap is still `evi-root-mismatch-rejects` alone. Distinct conditions
are unchanged at thirteen because three of the four new vectors reuse a condition (Finding 39);
`SET SCOPE` is a new designation, and its one vector is root-bearing, so `Remaining` does not move.

**No count in this table is written by hand anywhere in the package.** Every group count, the
vector total, and the entry census are derived by equality from the emitted set at build time
(`census()` in the generator, emitted as `header.census`), and the cross-check recomputes all of
them from the shipped file and fails on any disagreement. Rev 6's E-1 and rev 7's E-4 were both
hand-written counts that disagreed with their own artifact; E-5 above is a third. This closes the
class rather than correcting a third instance of it.

**Entry census, derived the same way and stated because it is the evidence for "the rev 7 set could
not fail":** 67 entry objects, 54 pinned, 13 unpinned, across 12 vectors carrying at least one
unpinned entry. The same walker over the rev 7 file gives 59 / 51 / 8 / 8, which reproduces
Michael's independently reported rev 7 census exactly. The four new vectors add the 5 unpinned and
3 pinned entries that account for the difference.

---

## Findings ledger — 35–39

| # | Finding | Source | Disposition |
|---|---|---|---|
| E-5 | Rev 7 l.111 says "twelve identifiers" over a table of thirteen | this side, rev 6 E-1's class | **Corrected** — l.111 reads thirteen; rev 8's counts are derived, not written. |
| E-6 | Rev 6 l.229/240 attribute Finding 12 to rev 5; it is rev 2 l.91–97 | this side | **Corrected** — attribution moved to rev 2. |
| E-7 | The rev 7 README quotes a fixture digest that does not match the file, runs the rev 6 files, and states rev 6's expected figures | this side, rev 6 E-2's class | **Corrected in the rev 8 README** — Reproduce block executed from a clean checkout before its digest was written. Rev 7 not edited. |
| 35 | The entry-identity rule is stated in the leaf preimage's terms, so unpinned entries read as out of scope | `headlessoracle` | **Normative amendment** — §4.3 (a) restated over all of `sources`; 24c's cross-reference corrected. |
| 36 | The set-level `retrieved_at` comparison borrows §4.1.2's pinned-only "canonical order" | `headlessoracle` | **Normative amendment** — bytewise-least over all entries; rev 2 l.95's domain restored. |
| 37 | The `retrieved_at` form rule does not say which entries it ranges over | `headlessoracle` | **Normative amendment** — every entry, before any branch on `pinned`; set-level form is transitive. |
| 38 | `pinned_set_empty` and `set_retrieved_at_not_first_in_canonical_order` name subsets their triggers do not use | `headlessoracle` (first), consequential (second) | **Normative amendment** — both renamed, superseded identifiers published, build fails on stale use. |
| 39 | Rev 7's build asserted one condition per vector was one vector per condition | this side, found while building rev 8 | **Assertion withdrawn** — conditions may repeat across vectors; superseded-identifier check replaces uniqueness. |
| — | Four vectors for 35, 36, and 37 | this side, for `headlessoracle`'s findings | **New vectors** — each proved discriminating at build time. |

**Attribution.** Findings 35, 36, 37, and the `pinned_set_empty` half of Finding 38 are Michael
Msebenzi's, reported against rev 7 on 2026-09-11 with the implementation lines that show his
reading. The diagnosis that all of them are one drafting habit — set-level rules written in
§4.1.2's pinned-only vocabulary — the second rename, Findings 39, E-5, E-6, and the four vectors
are this side's. Pablo Play's opposing reading of Finding 35 is what establishes that the rev 7
text is genuinely ambiguous rather than merely misread; **neither reading was a defect in either
implementation.**

---

## What remains open

1. **Five more all-versus-pinned scope choices.** Michael reported seven; this revision rules the
   three he named (Findings 35, 36, and the first half of 38) and holds the rest. **Rev 8 is not
   final until the five land and are ruled here.** Reserved as Findings 40–44 and deliberately left
   unnumbered against specific rules until his list arrives, so the numbering survives whatever
   the five turn out to be. The presumption from three instances is that the same repair applies —
   state the rule over `sources` in its own terms — but a presumption is not a ruling, and each
   needs its own text, its own condition identifier, and its own discriminating vector.
2. **The condition-enumeration diff** (rev 7 open item 1). Still open, unaffected by Finding 39:
   diff the thirteen named conditions against the malformed-condition enumeration in the
   specification text, whose count Michael puts at fifteen, and name the conditions with no vector.
3. **A cold build** (rev 7 open item 2). Unchanged and load-bearing. Michael's rev 7 run extended
   his earlier implementation; Pablo Play's from-text reconstruction is the filing gate for -02.
   **Until it lands, no revision of this section has had an independent implementation in the sense
   the README defines.**
4. **Michael's counterfactual variant builds.** He reported four builds producing byte-identical
   output at sha256 `d461aaf4…`; that digest is verified against
   `walker/evidence-roots-ours-rev7.json` at his tip `4689b38`, but the variant runs themselves are
   not committed there. Nothing in this revision depends on them.
