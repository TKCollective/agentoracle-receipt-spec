# Evidence pinning — amendments rev 8 for `draft-krausz-verification-state-02`

**Status: FINAL. Cut as rev 8, in one revision. Not filed, not pushed — filing is -02's step, gated
separately below.**

**Opened 2026-09-11, held for Michael Msebenzi's remaining scope choices, closed 2026-09-17 when
his full seven-item report landed.** The held draft ruled three of seven all-versus-pinned scope
choices (Findings 35–37) and reserved the rest. This revision rules the remaining five
(Findings 41–45), adds the premise that makes "pinned and unpinned alike" a sound reading of any of
them (Finding 40, the three-valued MUST), and adds one further defect his report surfaced in the
same pass (Finding 46, the null-snippet halt condition). **All eight items land in this one
revision, as instructed — not split across rev 8 and a later rev.**

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

**No revision-number bump for this closing pass.** The rev 7→rev 8 boundary already took the
semantics-change rename (below) for the reading change ruled in Findings 35–37. Findings 40–46 land
inside the still-unfiled rev 8 — nothing with rev 8's name and this content has been read by a third
party as conformant yet, so there is no prior surface to silently redefine. Completing a
held-but-unpublished revision is the defect-fix case in the sense of the filename convention, and
reuses the revision number. The filename's date suffix carries this pass's cut date, 2026-09-17, the
same convention rev 7's filename took at its own cut date (2026-09-09) — the suffix names when the
revision was cut, not when it was opened. A future rev 9 would take its own new filename and its own
cut-date suffix.

**New filename per `semantics_change_new_filename.md`, taken at rev 7→rev 8.** This revision changes
what a conformant implementation is checked against: two rules move from a pinned-only reading to a
whole-of-`sources` reading, two condition identifiers are renamed, and vectors are added that a
rev 7-conformant implementation reading those rules as pinned-only **passes today and fails here**.
Rev 7 and rev 8 are not interchangeable.

---

## Why this revision exists

**Both open questions ruled first (Findings 35–37) are set-level rules expressed in §4.1.2's
pinned-only vocabulary, and the fix is to stop borrowing it.** §4.1.2 defines one thing — a sort over
pinned leaves, because only pinned entries have leaves — and it defines it well. Three later rules
that range over `sources` were then written in its words: "identical across the members bound by the
leaf preimage," "first in canonical order," the condition name `pinned_set_empty`. Each borrowed
phrase silently narrowed a set-level rule to the pinned subset, and each is repaired the same way:
state the rule in its own terms, over `sources`, and cite §4.1.2 only where a sort over leaves is
actually meant.

**The five remaining choices (Findings 41–45) are the same habit, one level down.** Where Findings
35–37 are about which entries a *set-level comparison* ranges over, Findings 41–45 are about which
entries a *derivation* falls back to when a declared count or flag is absent: `fully_pinned` (check
5), the root-presence checks (checks 12/13), `resolveEvidenceSet`'s carried triple, and step (d)'s
per-item reasons all have a stated rule for the declared case and are silent on the absent one. The
same repair applies — derive from `sources` itself rather than leaving a gap — but the repair is only
sound because of Finding 40: without a closed `pinned` domain, "derive from the entries themselves"
does not have a well-defined pinned/unpinned split to derive over.

**Finding 40 is the premise underneath all of it, not a seventh instance of the same class.** Every
rule this revision or rev 7 states as "every entry, pinned and unpinned alike" presumes exactly two
buckets. Nothing in base through rev 7 requires `pinned` to be present or requires it to be a JSON
boolean. An entry that omits it, or spells it as the string `"true"`, is neither bucket — and a
conforming implementation that branches on `pinned === true` / `pinned === false` (the pattern in
`tools/evidence-root.ts`) treats that entry as the `false` branch by default, which is silent
scope-widening in the opposite direction from Findings 35–37's silent narrowing. Finding 40 closes it
before Findings 41–45 need it to be closed.

**Finding 46 is a defect this revision found while proving Finding 40's fixtures, not a scope
choice.** A pinned entry with `snippet_sha256` null or absent is not rejected by either check in
`validateEvidenceSet`'s pinned branch (checks 9–10 are the whole of it, and neither tests
`snippet_sha256`), and the omission is only discovered three functions later, as an uncaught
exception in `leafHash` whose message ("an unpinned entry has no leaf") misattributes the fault to
the wrong branch. Reproduced live against `tools/evidence-root.ts`. base l.99–100 already requires
the member on a pinned entry; the gap is that nothing enforces it as a halt at validation time.

**How the questions arrived.** Michael Msebenzi (`headlessoracle` / `LembaGang` in the findings
ledgers) reported on 2026-09-11 that his rev 7 implementation reads the entry-identity and
set-level-`retrieved_at` rules over the full set, and gave the code: `tools/evidence-root.ts` check
11 iterates `set.sources` with the four-member bound tuple, and for an unpinned entry the key
collapses so two unpinned entries sharing `url` and `retrieved_at` halt with `duplicate_bound_tuple`.
Pablo Play, reading the same text, took the pinned-only reading on the entry-identity rule. **Both
implementations passed all 32 rev 7 vectors.** He returned on 2026-09-17 with the remaining five
scope questions (checks 5, 10, 12/13, `resolveEvidenceSet`, step (d)), the two implementation
defects (check 4 unreachable; the null-snippet exception), confirmation that F24, F32a, and F32b
still hold against his current tip, a report of three committed counterfactual variant builds at
commit `77381b9`, and closed with the three-valued-`pinned` finding.

**What is now confirmed for this run, updated from the held draft.** The held draft (2026-09-11)
recorded that the four counterfactual variant builds were reported but "not committed at his tip
`4689b38`." They are now committed, at `77381b9` in `LembaGang/receipt-verify`, co-authored by
"Claude Opus 5 (1M context)": three counterfactual builds (f24, f32a, f32b), all producing a
byte-identical output digest `d461aaf4d6e4964d4176a3f9f717d49b8faf506bb772df350f8229760e50e451`
(git blob `1c8d207a…`), independently re-verified this pass — `npm install` in a clean checkout,
all three builds and probes executed, 3/3 probes hold, and the negative control correctly fails when
one of the three values is reverted. **What is still not claimed:** this is a confirmed-by-extension
run against his existing implementation, not an independent from-text cold build. Pablo Play's
cold-build reconstruction remains the open filing gate — see "What remains open" below.

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

## Note — check 4 in the reviewed implementation is dead code, not a scope decision

Michael reported check 4 (`pinned_count` exceeds `source_count`, `tools/evidence-root.ts` l.352–358)
as unreachable, given checks 2 (l.340) and 3 (l.347) already halt on any input that would trigger it,
and reports it deleted from his tree. **This is not a rule this specification states and now
retracts.** Nothing in base through rev 7 names a `pinned_count`-exceeds-`source_count` condition
independent of checks 2/3's own triggers, and no vector in any revision through rev 8 targets one.
The deletion is informational about the reviewed implementation's own code health, not a spec
amendment, and this document makes no normative change on account of it. Recorded here so it is not
mistaken later for a dropped requirement.

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
covers that pair**, and it remains a candidate for a future revision rather than something rev 8
claims to have exercised.

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

Not a scope choice and not reported by a reviewer: found while building rev 8, and recorded
because it changes a shipped build assertion.

Rev 7's Finding 33 requires that every `MALFORMED` vector name **exactly one** condition. Correct,
and unchanged. Alongside it, the rev 7 generator and cross-check also assert that **no two vectors
name the same condition** — which was true of the rev 7 set by accident of construction, one vector
having been written per condition, and was never stated as a rule.

Rev 8's set makes it false on purpose, and this closing pass makes it false again in a new place:
the original four rev-8 vectors inject an already-vectored condition on a different entry class
(`duplicate_bound_tuple` on two unpinned entries; `retrieved_at_not_canonical_form` on an unpinned
entry; `set_retrieved_at_not_bytewise_least` with the lesser value on an unpinned entry), and
Finding 42 below does the same thing again: `snippet_digest_present_for_full_resource` is named by
both the existing pinned vector and the new unpinned one. Injecting the same condition from a
different direction is exactly how a scope rule gets covered, so the uniqueness assertion would
fail a correct set.

**Amendment.** The uniqueness assertion is **withdrawn**. Every `MALFORMED` vector still names
exactly one condition; a condition may be named by more than one vector; and what replaces
uniqueness in the build is a check that no vector names a **superseded** identifier (Finding 38).
The condition-enumeration diff that rev 7 opens for rev 8 is unaffected — it compares the *set* of
named conditions against the enumeration in the specification text, and a set does not care how
many vectors reach each member.

## Finding 40 — `pinned` is REQUIRED and MUST be exactly `true` or `false`: the third case is closed

Base through rev 7 never state that `pinned` must be present on a `sources` entry, nor that it must
be a JSON boolean. Michael's report: a conforming implementation branching `pinned === true` /
`pinned === false` (his read of `tools/evidence-root.ts` l.256, l.344, l.533 for the true branch and
l.393 for the false branch) treats an entry that omits `pinned`, or spells it non-booleanly (for
example the string `"true"`), as falling through to the `false` branch by default — not as a halt.

**This is the premise every "pinned and unpinned alike" rule in this document depends on.** Findings
35–37, already ruled above, and Findings 41–45 below all state a rule "over every entry, pinned and
unpinned alike." That phrasing is sound only if every entry is provably one or the other. Without
this finding, "alike" silently presumes a binary the corpus never actually stated, and an entry with
`pinned` absent is neither counted nor excluded by any of those rules — it is simply unaddressed.

**Amendment — add to base §4.1.1 (per-entry members, base l.83–103):**

> `pinned` is a REQUIRED member of every entry in `sources` and MUST be exactly the JSON value
> `true` or `false`. An entry where `pinned` is absent, `null`, or of any type other than boolean is
> malformed; gate decision = halt; reported condition `pinned_absent_or_not_boolean`. This closes
> the domain of `pinned` to exactly two values before any rule that branches on it, or that is
> stated as ranging "over every entry, pinned and unpinned alike," is evaluated — including
> Findings 35–37 above and Findings 41–45 below, none of which are well-defined against a `pinned`
> domain that admits a third, unaddressed case.

**Vectors:** `evi-pinned-absent-rejects` (the member omitted entirely) and
`evi-pinned-not-boolean-rejects` (`pinned: "true"`, a JSON string, not a boolean). Both `MALFORMED`,
both reporting `pinned_absent_or_not_boolean`. One condition, because the trigger — `pinned` is not
exactly the boolean `true` or the boolean `false` — is one predicate over one member; splitting it
into two condition identifiers would name the two ways to fail the predicate rather than the
predicate itself, which Finding 34 already forbids.

## Finding 41 — `fully_pinned`'s consistency check falls back to the entries when its operands are absent (was check 5)

Rev 2 l.180–181 (base l.74) states `fully_pinned`'s consistency against `source_count` and
`pinned_count` when both are declared, and is silent on the case where one or both are absent.
`tools/evidence-root.ts` check 5 (l.363–364) reads the declared members only, so an evidence set that
omits `source_count` and `pinned_count` and declares `fully_pinned` skips the check entirely rather
than falling back to a value it could still verify.

**The fallback is well-defined only because of Finding 40.** `source_count`, when absent, is
`len(sources)` — unconditionally, since `sources` always has a length regardless of what any entry's
`pinned` says. `pinned_count`, when absent, is the count of entries with `pinned: true` — and this
count is well-defined, rather than undercounting an ambiguous third bucket, exactly because Finding
40 has already closed `pinned` to two values.

**Amendment — add to rev 2's fully_pinned consistency text (base l.74, rev 2 l.180–181):**

> When `source_count` is absent from the evidence set, its operand for this check is
> `len(sources)`. When `pinned_count` is absent, its operand is the count of entries in `sources`
> with `pinned: true` (well-defined per Finding 40). `fully_pinned`'s consistency is checked
> against these derived operands whenever the corresponding declared member is absent; the check is
> not skipped for want of a declared count.

**Vector:** `evi-fully-pinned-fallback-derives-from-sources-accepted`, `ADDITIVE`. Three entries
(two pinned, one unpinned), `source_count` and `pinned_count` both omitted, `fully_pinned: false`
declared. Derived operands are `source_count=3`, `pinned_count=2`; `fully_pinned=false` is
consistent with a non-fully-pinned set, and the set is accepted, not malformed for want of the
declared counts.

## Finding 42 — the full-resource/resource_sha256 rule ranges over every entry, and the rev 7 set only exercised the pinned branch (was check 10)

Rev 4 l.249–254 (Finding 19) states that a `content_kind` of `full_resource` together with a
non-null `resource_sha256` is malformed, and names no pinned-only restriction — the rule is one
about what `content_kind` and `resource_sha256` may say together, not about `pinned`. `Michael's
tools/evidence-root.ts` check 10 (l.418–424) sits after the unpinned branch's `continue` at l.402,
so an unpinned entry that nonetheless carries `content_kind: "full_resource"` and a non-null
`resource_sha256` never reaches the check that would reject it — not because the rule excludes
unpinned entries, but because of where the check is placed in his implementation.

**This is the pinned-only-placement class, not a new rule.** The condition being tested —
`content_kind` says `full_resource` while a resource digest is also present — does not mention
`pinned` at all, and Finding 40 makes an unpinned entry's `content_kind`/`resource_sha256` members
just as determinate as a pinned entry's, so F19 applies to it unchanged.

**Amendment — amend rev 4's Finding 19 text (base l.249–254) to state explicitly:**

> This rule ranges over every entry in `sources` regardless of `pinned`. `content_kind` and
> `resource_sha256` are per-entry members whose joint value this rule constrains directly; nothing
> in the rule's own statement is conditioned on `pinned`, and an implementation MUST evaluate it for
> an unpinned entry exactly as for a pinned one.

**Vector:** `evi-full-resource-digest-on-unpinned-rejects`, `MALFORMED`, reporting
`snippet_digest_present_for_full_resource` — the same condition identifier as the existing pinned
vector `evi-resource-sha256-with-full-resource-rejects` (Finding 39's reuse pattern), now injected on
an unpinned entry that an implementation placing the check inside the pinned branch would not reach.

## Finding 43 — the root-presence checks fall back to the entries when `pinned_count` is absent (was checks 12/13)

Base l.139–140 and rev 2 l.186–188 state the zero-pinned/nonzero-pinned root rules against the
*declared* `pinned_count` and are silent on an absent one. The operand, when `pinned_count` is
absent, is the same fallback as Finding 41: the count of entries with `pinned: true`,
well-defined by Finding 40.

**Amendment — add to base l.139–140 / rev 2 l.186–188:**

> When `pinned_count` is absent from the evidence set, both this rule and the nonzero-pinned/null-
> root rule at rev 2 l.186–188 take their `pinned_count` operand as the count of entries in
> `sources` with `pinned: true` (Finding 40). A non-null `evidence_root` with a derived
> `pinned_count` of zero is `root_present_with_zero_pinned`; a null `evidence_root` with a derived
> `pinned_count` greater than zero is `root_null_with_pinned_entries`. Neither rule is skipped for
> want of a declared `pinned_count`.

**Vector:** `evi-root-present-pinned-count-absent-accepted`, `ADDITIVE`. Two entries (one pinned, one
not), `pinned_count` omitted, `evidence_root` present and equal to the correct root over the pinned
entry alone (checked against `computed.correct_root`, recomputed independently by the Node
cross-check). Derived `pinned_count` is 1, nonzero, so a non-null root is accepted rather than
flagged as a zero-pinned violation.

## Finding 44 — `resolveEvidenceSet` derives all three carried members from the entries when they are absent (was resolveEvidenceSet's triple fallback)

Rev 2 l.190–193 speaks of a *carried* `fully_pinned` at the resolution step and states no derivation
for an absent one. `tools/evidence-root.ts`'s `resolveEvidenceSet` (l.533–536) reads `source_count`,
`pinned_count`, and `fully_pinned` as carried inputs; when all three are absent, resolution has
nothing to carry and — per Michael's report — the implementation does not derive them, leaving the
step without the values Findings 41 and 43 already establish are derivable.

**Same derivation shape as Findings 41 and 43, now at the resolution step.** When all three are
absent, `source_count` derives to `len(sources)`, `pinned_count` derives to the count of
`pinned: true` entries, and `fully_pinned` derives to whether that count equals `source_count` —
each well-defined by Finding 40, and each already the fallback this document establishes for the
validation-time checks. Resolution should not re-open a question validation has already answered by
falling back to declared-only reads.

**Amendment — add to rev 2 l.190–193:**

> When `source_count`, `pinned_count`, and `fully_pinned` are all absent from the evidence set,
> `resolveEvidenceSet` derives them from `sources` using the same fallbacks as Findings 41 and 43:
> `source_count = len(sources)`, `pinned_count` = the count of entries with `pinned: true`, and
> `fully_pinned` = (`pinned_count == source_count`). Resolution proceeds on these derived values;
> it MUST NOT halt for want of declared count members that validation has already shown are
> derivable.

**Vector:** `evi-resolve-all-counts-absent-accepted`, `RESOLUTION`. Two pinned entries,
`source_count`, `pinned_count`, and `fully_pinned` all omitted, verifier holds bytes for both URLs
and content matches. Derived values are `source_count=2`, `pinned_count=2`, `fully_pinned=true`; the
step resolves on them (root checked against `computed.evidence_root`, recomputed independently)
rather than halting for want of the declared members.

## Finding 45 — step (d)'s per-item reasons range over every entry, including the trivial unpinned case (was step (d))

Rev 4 l.184–191 (Finding 17) states that step (d) reports a per-item reason and names no pinned
restriction — `item_reasons` is per-entry, not per-pinned-entry. An unpinned entry trivially
qualifies for `content_not_held` — by definition it was never retained, so the verifier never holds
candidate bytes for it — and the open question was whether that trivial case still needs to appear
in `item_reasons`, or whether it may be omitted because the entry was already unpinned and so
"obviously" `content_not_held`.

**It must appear, and omitting it is exactly the class this revision keeps closing.** F17 is stated
per-item and unconditioned on `pinned`; an implementation that omits unpinned entries from
`item_reasons` because their reason is "trivial" is applying an unstated pinned-only restriction to
a set-level output, the same shape as Findings 35–37 and 41–44. This finding does not, and cannot,
change the resolution token itself: a set carrying any unpinned entry already resolves `unknown`
before step (d) runs (rev 5 Finding 17's UNKNOWN pair), so the token is settled upstream of this
finding either way.

**Amendment — add to rev 4's Finding 17 text (base l.184–191):**

> Step (d) reports a per-item reason for every entry in `sources`, pinned and unpinned alike. An
> unpinned entry's reason is `content_not_held`, true by construction since an unpinned entry was
> never retained (rev 4 l.294–296); this is not exempted from `item_reasons` for being trivial or
> for the entry being unpinned. Omitting an unpinned entry from `item_reasons` is malformed output
> from a conforming verifier, distinct from the receipt's own gate decision.

**Vector:** `evi-unpinned-item-reason-content-not-held`, `UNKNOWN`. A single unpinned entry with no
candidate bytes held; expects `content_not_held` reported in `item_reasons` for that entry itself,
not omitted on the basis that the entry is unpinned.

## Finding 46 — step (a) MUST halt on a pinned entry with an absent or null `snippet_sha256`, not surface as an uncaught exception

base l.99–100 already requires `snippet_sha256` on a pinned entry. Michael's report: neither check
in `validateEvidenceSet`'s pinned branch (checks 9–10, l.418–424, the whole of that branch) tests
`snippet_sha256` at all, so a pinned entry with the member null or absent passes step (a) and
reaches `resolveEvidenceSet`/`computeRoot`, where `leafHash` throws an uncaught exception. Reproduced
live against `tools/evidence-root.ts`: the thrown message is "an unpinned entry has no leaf," which
misattributes the fault — the entry that failed is pinned, and the actual defect is a null leaf
input, not an unpinned entry reaching leaf construction at all.

**This is a gap in the halt surface, not a new normative requirement** — the member was already
required. What is new is that step (a) MUST test for it, so the failure is a reported halt with a
condition identifier rather than an uncaught exception discovered downstream, three function calls
after the point where the input was already known to be malformed.

**Amendment — add to base §4.2 (a) (step (a), the pinned-branch checks):**

> Step (a) MUST reject a pinned entry (`pinned: true`) whose `snippet_sha256` is absent or `null`,
> before any resolution or root computation is attempted. Gate decision = halt; reported condition
> `snippet_sha256_absent_when_pinned`. This is a validation-time halt, not a runtime exception: an
> implementation MUST NOT allow a malformed input of this shape to reach leaf or root construction
> and rely on a downstream error to surface it.

**Vector:** `evi-snippet-sha256-absent-when-pinned-rejects`, `MALFORMED`, `snippet_sha256_absent_when_pinned`.
A pinned entry with `snippet_sha256: null`. Expects a halt at step (a); explicitly must not reach
`leafHash`/`computeRoot` and must not surface as an uncaught exception.

---

## Vectors for the rules this revision scopes

The original four rev-8 vectors (Findings 35–37) and the eight added in this closing pass (Findings
40, 42, 43, 44, 45, 46 above — Findings 41 and 43's derivation shape share one condition-free
`ADDITIVE`/`RESOLUTION` pattern rather than each minting a new condition identifier) total twelve new
vectors over the rev 7 set. **The point of each is the same: the rev 7 set of 32 cannot fail on it,**
and for Findings 35–37 specifically, `assert_scope_discriminating` proves it by evaluating the
vector's own input under both competing readings and failing if they agree.

### Findings 35–37 (carried from the held draft, unchanged)

- `evi-duplicate-unpinned-entries-rejects` — `MALFORMED`, `duplicate_bound_tuple`
- `evi-unpinned-retrieved-at-noncanonical-rejects` — `MALFORMED`, `retrieved_at_not_canonical_form`
- `evi-set-retrieved-at-equals-unpinned-value` — `SET SCOPE`, accepted, root-bearing
- `evi-set-retrieved-at-above-unpinned-value-rejects` — `MALFORMED`, `set_retrieved_at_not_bytewise_least`

### Findings 40–46 (this closing pass)

- `evi-pinned-absent-rejects` — `MALFORMED`, `pinned_absent_or_not_boolean` (Finding 40)
- `evi-pinned-not-boolean-rejects` — `MALFORMED`, `pinned_absent_or_not_boolean` (Finding 40)
- `evi-fully-pinned-fallback-derives-from-sources-accepted` — `ADDITIVE`, accepted (Finding 41)
- `evi-full-resource-digest-on-unpinned-rejects` — `MALFORMED`, `snippet_digest_present_for_full_resource` (Finding 42)
- `evi-root-present-pinned-count-absent-accepted` — `ADDITIVE`, accepted, root-bearing (Finding 43)
- `evi-resolve-all-counts-absent-accepted` — `RESOLUTION`, accepted, root-bearing (Finding 44)
- `evi-unpinned-item-reason-content-not-held` — `UNKNOWN` (Finding 45)
- `evi-snippet-sha256-absent-when-pinned-rejects` — `MALFORMED`, `snippet_sha256_absent_when_pinned` (Finding 46)

**Finding 34 compliance.** None of the new `expect` strings name the resolution being tested as
though it were the input; each names the input configuration (which member is absent, which entry
class carries the condition) and cites the governing finding for the rule, not the ruling itself.

**Cross-language agreement, executed for real this pass — not asserted.**
`fixtures/evidence-pinning-fixture-crosscheck-rev8.mjs --check
fixtures/evidence-pinning-fixtures-v2-rev8.json` was run against the regenerated 44-vector set:
`total_roots_checked: 26` (24 raw children, 1 hex-child counter-construction, 1 leaf raw-digest
counter-construction), `vectors_in_file: 44`, `mismatches: 0`, `all_agree: true`. Two of the new
vectors' `computed` root keys (`evi-root-present-pinned-count-absent-accepted`,
`evi-resolve-all-counts-absent-accepted`) were matched to the cross-check's existing dispatch rules
for `correct_root` and `evidence_root` respectively — no new dispatch branch was needed, and no new
branch was added. **The fixture bundle's own digests are pinned in
`fixtures/evidence-pinning-fixture-README-rev8.md`, not repeated here** — this document's digest is
the input to that pin, not the other way around, and quoting the fixture set's hash here would make
this document's own hash depend on a value that in turn depends on this document's hash.

---

## Set size after this revision

| | rev 7 | rev 8 (held, 2026-09-11) | rev 8 (final, 2026-09-17) |
|---|---|---|---|
| Total vectors | 32 | 36 | **44** |
| Root-bearing vectors | 13 | 14 | **16** |
| Root values carried | 23 | 24 | **26** |
| `MALFORMED` | 13 | 16 | **20** |
| Remaining (all other designations) | 7 | 7 | **9** |
| Overlap (`MALFORMED` **and** root-bearing) | 1 | 1 | **1** |
| Distinct conditions named | 13 | 13 | **15** |

16 + 20 + 9 − 1 = 44. The overlap is still `evi-root-mismatch-rejects` alone. Two condition
identifiers are new in this closing pass — `pinned_absent_or_not_boolean` (Finding 40) and
`snippet_sha256_absent_when_pinned` (Finding 46); Finding 42's `snippet_digest_present_for_full_resource`
reuses an identifier already named by the existing pinned vector, per Finding 39.

**No count in this table is written by hand anywhere in the package.** Every group count, the
vector total, and the entry census are derived by equality from the emitted set at build time
(`census()` in the generator, emitted as `header.census`), and the cross-check recomputes all of
them from the shipped file and fails on any disagreement. Rev 6's E-1 and rev 7's E-4 were both
hand-written counts that disagreed with their own artifact; E-5 above is a third. This closes the
class rather than correcting a third instance of it.

**Entry census, derived the same way:**

| | rev 7 | rev 8 (held) | rev 8 (final) |
|---|---|---|---|
| Entry objects | 59 | 67 | **79** |
| Pinned entries | 51 | 54 | **62** |
| Unpinned entries | 8 | 13 | **17** |
| Vectors carrying ≥1 unpinned entry | 8 | 12 | **16** |

The rev 7 figures reproduce Michael Msebenzi's independently reported rev 7 census exactly
(59 / 51 / 8 / 8). The twelve vectors added since rev 7 account for the full deltas.

---

## Findings ledger — 35–46

| # | Finding | Source | Disposition |
|---|---|---|---|
| E-5 | Rev 7 l.111 says "twelve identifiers" over a table of thirteen | this side, rev 6 E-1's class | **Corrected** — l.111 reads thirteen; rev 8's counts are derived, not written. |
| E-6 | Rev 6 l.229/240 attribute Finding 12 to rev 5; it is rev 2 l.91–97 | this side | **Corrected** — attribution moved to rev 2. |
| E-7 | The rev 7 README quotes a fixture digest that does not match the file, runs the rev 6 files, and states rev 6's expected figures | this side, rev 6 E-2's class | **Corrected in the rev 8 README** — Reproduce block executed from a clean checkout before its digest was written. Rev 7 not edited. |
| — | Check 4 (`pinned_count` exceeds `source_count`) is unreachable given checks 2/3, deleted from the reviewed implementation | `headlessoracle` | **Noted, not a spec amendment** — dead code in the reviewed implementation, not a rule this specification ever stated independently of checks 2/3. |
| 35 | The entry-identity rule is stated in the leaf preimage's terms, so unpinned entries read as out of scope | `headlessoracle` | **Normative amendment** — §4.3 (a) restated over all of `sources`; 24c's cross-reference corrected. |
| 36 | The set-level `retrieved_at` comparison borrows §4.1.2's pinned-only "canonical order" | `headlessoracle` | **Normative amendment** — bytewise-least over all entries; rev 2 l.95's domain restored. |
| 37 | The `retrieved_at` form rule does not say which entries it ranges over | `headlessoracle` | **Normative amendment** — every entry, before any branch on `pinned`; set-level form is transitive. |
| 38 | `pinned_set_empty` and `set_retrieved_at_not_first_in_canonical_order` name subsets their triggers do not use | `headlessoracle` (first), consequential (second) | **Normative amendment** — both renamed, superseded identifiers published, build fails on stale use. |
| 39 | Rev 7's build asserted one condition per vector was one vector per condition | this side, found while building rev 8 | **Assertion withdrawn** — conditions may repeat across vectors; superseded-identifier check replaces uniqueness. |
| 40 | `pinned` may be absent or non-boolean; nothing closes it to two values before rules branch on it | `headlessoracle` | **Normative amendment** — `pinned` REQUIRED, MUST be boolean; halt otherwise. Premise for every "pinned and unpinned alike" rule in this document. |
| 41 | `fully_pinned`'s consistency check (was check 5) has no fallback when `source_count`/`pinned_count` are absent | `headlessoracle` | **Normative amendment** — falls back to `len(sources)` and the `pinned: true` count. |
| 42 | The full-resource/`resource_sha256` rule (was check 10) sits after the unpinned-branch `continue` in the reviewed implementation | `headlessoracle` | **Normative amendment (clarifying placement)** — rule ranges over every entry regardless of `pinned`; no pinned-only restriction was ever stated. |
| 43 | The root-presence checks (was checks 12/13) have no fallback when `pinned_count` is absent | `headlessoracle` | **Normative amendment** — same fallback as Finding 41, applied to root-presence. |
| 44 | `resolveEvidenceSet`'s carried triple has no fallback when all three members are absent | `headlessoracle` | **Normative amendment** — derives all three from `sources`; resolution does not re-open what validation already answers. |
| 45 | Step (d)'s per-item reasons (was step (d)) — is the trivial unpinned `content_not_held` case exempt from `item_reasons`? | `headlessoracle` | **Normative amendment** — not exempt; every entry, including the trivial unpinned case, gets a reported reason. |
| 46 | A pinned entry with absent/null `snippet_sha256` passes step (a) and later throws an uncaught exception in `leafHash`, misattributed to the wrong branch | `headlessoracle` | **Normative amendment (closes a halt-surface gap)** — step (a) MUST halt on this shape; new condition `snippet_sha256_absent_when_pinned`. |
| — | Twelve vectors for Findings 35–37 and 40–46 | this side, for `headlessoracle`'s findings | **New vectors** — Findings 35–37 proved discriminating at build time; Findings 40–46 cross-checked in Node against the regenerated 44-vector set, 0 mismatches. |

**Attribution.** Every numbered finding in this ledger (35–46) is Michael Msebenzi's, reported
against `tools/evidence-root.ts` across two messages on 2026-09-11 and 2026-09-17, with the
implementation lines that show his reading in each case. The diagnosis that Findings 35–37 are one
drafting habit, the second condition rename, Finding 39, E-5, E-6, E-7, the "check 4 is dead code,
not a scope decision" note, and the twelve vectors are this side's. Pablo Play's opposing reading of
Finding 35 is what establishes that the rev 7 text was genuinely ambiguous rather than merely
misread; **neither reading was a defect in either implementation.**

---

## What remains open

1. **A cold build.** Unchanged and load-bearing. Michael's runs across rev 5 through this pass all
   extend his earlier implementation; Pablo Play's from-text reconstruction is **the filing gate for
   -02**. **Until it lands, no revision of this section has had an independent implementation in the
   sense the README defines.**
2. **The condition-enumeration diff** (rev 7 open item 1, carried unchanged). Fifteen conditions are
   now named by vectors (up from thirteen), which happens to match the fifteen Michael previously put
   the specification text's malformed-condition enumeration at — but that match is not verified here
   against his actual list, and this document does not claim the diff is closed on that basis. Still
   open until the two lists are actually compared name-for-name.
3. **The pinned+unpinned duplicate-identity pair** (noted under Finding 35). A pinned entry and an
   unpinned entry sharing `url` and `retrieved_at` is one retrieval recorded twice under the amended
   §4.3 (a), and no vector in this revision covers that pair. Candidate for a future revision.
4. **Michael's counterfactual variant builds** — resolved this pass, no longer open. Confirmed
   committed at `77381b9` and independently re-verified (clean install, all three builds and probes
   run, 3/3 hold, negative control fails correctly). Recorded above under "What is now confirmed."

Item 1 in the held draft's original list — "five more all-versus-pinned scope choices" — is
**resolved by this revision** (Findings 40–46) and is not carried forward.
