# evidence-pinning fixtures — v2 preimage, rev 8 rules

**Status: FINAL. Rev 8 is cut. Not independently implemented — see the disclosure below before
citing this bundle in any external message.**

Forty-four conformance vectors for the evidence-pinning section of
`draft-krausz-verification-state-02`, computed under `ao-evidence-leaf-v2` with the four-term
canonical order, the rev 5 distinctness rule, rev 6's normative node-child encoding, rev 7's
`condition` members and non-disclosing identifiers, and **rev 8's whole-of-`sources` scope rules,
now including the three-valued-`pinned` premise (Finding 40) and the five derivation-fallback and
placement findings it closes (Findings 41–45), plus the null-snippet halt condition (Finding 46).**

**Closed 2026-09-17.** Rev 8 was opened 2026-09-11 ruling three of Michael Msebenzi's seven
all-versus-pinned scope choices (Findings 35–37) and held for the remaining four items in his
report. His full report landed 2026-09-17 (checks 5, 10, 12/13, `resolveEvidenceSet`, step (d), the
three-valued-`pinned` finding, and the null-snippet exception); all of it lands in this one
revision, as instructed, rather than splitting across rev 8 and a later rev.

## Files

- `evidence-pinning-fixture-generator-rev8.py` — **reference generator.** The sole emitter of
  `evidence-pinning-fixtures-v2-rev8.json`.
- `evidence-pinning-fixture-crosscheck-rev8.mjs` — **Node cross-check.** Recomputes every root in
  the fixture file, recomputes the census, re-derives each Finding 35–37 vector's scope
  discrimination, and rejects superseded condition identifiers. Exits non-zero on any mismatch.
  Not an emitter, and **not a conformance verifier**: it checks that roots, census, and condition
  identifiers in the shipped file are internally consistent and correctly computed. It does not
  evaluate whether a vector's `input` actually triggers its declared `condition` — that is what the
  generator's `assert_scope_discriminating` (Findings 35–37 only) and manual review of each
  amendment's `expect` string are for.
- `evidence-pinning-fixtures-v2-rev8.json` — the emitted fixture set.

**New filenames taken at rev 7→rev 8** per `semantics_change_new_filename.md`; unchanged by this
closing pass, which completes the still-unpublished rev 8 rather than opening a rev 9. The rev 7
files stay on disk byte-unchanged.

## What changed since the held (2026-09-11) draft

| Vector | Change | Finding |
|---|---|---|
| `evi-pinned-absent-rejects` | **NEW.** `pinned` member omitted entirely. `MALFORMED`, `pinned_absent_or_not_boolean`. | 40 |
| `evi-pinned-not-boolean-rejects` | **NEW.** `pinned: "true"` (JSON string, not boolean). `MALFORMED`, `pinned_absent_or_not_boolean`. | 40 |
| `evi-fully-pinned-fallback-derives-from-sources-accepted` | **NEW.** `source_count`/`pinned_count` both omitted; `fully_pinned` checked against derived values. `ADDITIVE`, accepted. | 41 |
| `evi-full-resource-digest-on-unpinned-rejects` | **NEW.** `content_kind: full_resource` + `resource_sha256` on an *unpinned* entry. `MALFORMED`, `snippet_digest_present_for_full_resource` (reused). | 42 |
| `evi-root-present-pinned-count-absent-accepted` | **NEW.** `pinned_count` omitted, `evidence_root` present and correct. `ADDITIVE`, accepted, root-bearing. | 43 |
| `evi-resolve-all-counts-absent-accepted` | **NEW.** `source_count`, `pinned_count`, `fully_pinned` all omitted at resolution. `RESOLUTION`, accepted, root-bearing. | 44 |
| `evi-unpinned-item-reason-content-not-held` | **NEW.** Trivial `content_not_held` reason on the unpinned entry itself, must not be omitted. `UNKNOWN`. | 45 |
| `evi-snippet-sha256-absent-when-pinned-rejects` | **NEW.** Pinned entry, `snippet_sha256: null`. `MALFORMED`, `snippet_sha256_absent_when_pinned` (new). | 46 |

**All 36 vectors from the held draft are retained, byte-identical.** Eight vectors are added; no
existing vector's input, designation, `expect` string, condition, or root moves. Verified by
diffing the two emitted sets rather than by inspection of the patch.

**Two new condition identifiers** (`pinned_absent_or_not_boolean`, `snippet_sha256_absent_when_pinned`);
one existing identifier (`snippet_digest_present_for_full_resource`) is reused on a new entry class,
per Finding 39's already-established reuse pattern.

## Why these eight vectors exist

Michael Msebenzi's 2026-09-17 report closed his remaining five all-versus-pinned scope choices and
added two implementation defects and the three-valued-`pinned` finding. Findings 41–45 are all one
shape — a rule states its operand for the *declared* case and is silent on the absent one — and that
shape is only soundly closed once Finding 40 has made "the count of entries with `pinned: true`" a
well-defined fallback in the first place. Finding 46 is a distinct defect: a required member with no
enforcing check at validation time, discovered downstream as an uncaught exception rather than a
reported halt.

Unlike the four Finding 35–37 vectors, these eight are not scope-discriminating in the
`assert_scope_discriminating` sense — that mechanism proves a vector distinguishes two competing
*readings* of one ambiguous sentence, and Findings 40–46 are not textual ambiguities with two live
readings; they are gaps (an unaddressed case, a placement defect, a missing validation-time check).
Each vector's discriminating power is instead that **the rev-8-held (36-vector) set could not have
caught the defect it targets** — verified directly: none of the eight is a mutation of an existing
input, and no existing vector exercises `pinned` absent, `pinned` non-boolean, a null pinned
`snippet_sha256`, or any of the four absent-count-derivation shapes.

## Independence disclosure — read before citing

Both `evidence-pinning-fixture-generator-rev8.py` and `evidence-pinning-fixture-crosscheck-rev8.mjs`
were written by the same party. Agreement between them is a **cross-language check**: it catches
language-specific defects (JSON ordering, UTF-8 handling, hash-library differences, integer widths,
string comparison rules). It does **not** establish independence.

**Independence for this section means a build from the specification text alone by a party with no
access to these files.**

**No revision of this section has had one in that sense.** Michael Msebenzi's rev 5 run was
independent; his rev 6 through this pass's runs all extend that implementation rather than
rebuilding from text, so they are **confirmed-by-extension**. Pablo Play's from-text reconstruction
is the filing gate for -02 and has not landed. The rev 8 set — including these eight new vectors —
has had **no** implementer run of any kind.

Do not describe cross-language agreement in this bundle as independent implementation in any
external message, changelog, deposit, or public artifact.

### Superseded condition identifiers (unchanged from the held draft)

| superseded identifier (rev 7) | identifier (rev 8) |
|---|---|
| `pinned_set_empty` | `evidence_set_names_no_sources` |
| `set_retrieved_at_not_first_in_canonical_order` | `set_retrieved_at_not_bytewise_least` |

Both the generator and the cross-check **fail the build** if any vector names a superseded
identifier — verified below under "The fail paths were exercised."

## Spec bases

Re-derived from `TKCollective/agentoracle-receipt-spec` at
`3d0ec0e82229c1336340f0323d54904e5baf38b2` and compared byte-for-byte against the local copies.
All identical, except the rev 8 amendments document itself, whose digest changed with this closing
pass (below).

| Base | sha256 | bytes | lines |
|---|---|---|---|
| `drafts/evidence-pinning-02-review-draft.md` | `9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096` | 14,469 | 289 |
| `drafts/evidence-pinning-02-amendments-rev5-2026-09-06.md` | `1f901fd7d56fcfe9f858446e5b685b540b5904d6abcfb4b2509e1eb675aa1e51` | 14,631 | 256 |
| `drafts/evidence-pinning-02-amendments-rev6-2026-09-08.md` | `d62ded37dcf63f541e5b670b0cc0f7876e04a182064eb06a32af0037effaf026` | 21,968 | 412 |
| `drafts/evidence-pinning-02-amendments-rev7-2026-09-09.md` | `6b13f6fc35d745c2642edcb52a2754f7cd43340ded3248b5d1ba70a431d6c037` | 17,732 | 296 |
| `drafts/evidence-pinning-02-amendments-rev8-2026-09-11.md` (**final, this pass**) | `c42928e6b08f30828d7664f1abcb737431a13cbd19650b64e85b2365cc04636c` | 46,420 | 642 |

**The pin is one-directional: rev 8 must be final before the fixture is generated, and editing rev
8 afterwards leaves the pin stale and requires regeneration.** This pass's own history is the
demonstration: the pin was first set against a pre-final digest, drifted the moment the amendments
document text changed, and was caught and corrected before this README's digest was written —
recorded as this pass's own version of E-7's class, not repeated as a defect.

## Forty-four vectors

- 36 retained from the held draft (13 from rev 2, 8 from rev 4, 1 from rev 5, 1 from rev 6, 3 from
  rev 7, 4 from the held rev 8 pass — Findings 35–37)
- **8 added by this closing pass** (Findings 40–46, per the table above)

Not emitted: `evi-partial-pinning-honest` and `evi-recompute-claim-inconsistent-rejects` (removed in
rev 2 §8), and `evi-fully-pinned-zero-sources-rejects` (dissolved in rev 4 Finding 18b).

### Counting by function, and the overlap

| | rev 7 | rev 8 (held) | rev 8 (final) |
|---|---|---|---|
| Total vectors | 32 | 36 | **44** |
| Root-bearing vectors | 13 | 14 | **16** |
| Root values carried | 23 | 24 | **26** |
| `MALFORMED` | 13 | 16 | **20** |
| Remaining (all other designations) | 7 | 7 | **9** |
| Overlap (`MALFORMED` **and** root-bearing) | 1 | 1 | **1** |
| Distinct conditions named | 13 | 13 | **15** |

> **16 + 20 + 9 − 1 = 44.**

The overlap is still `evi-root-mismatch-rejects` alone. Two condition identifiers are new this pass
(`pinned_absent_or_not_boolean`, `snippet_sha256_absent_when_pinned`); one is reused
(`snippet_digest_present_for_full_resource`), per Finding 39.

**No count in this bundle is written by hand.** Every group count, the vector total, and the entry
census are derived by equality from the emitted set at build time (`census()` in the generator,
emitted as `header.census`), and the cross-check recomputes all of them from the shipped file and
fails on any disagreement. Rev 6's E-1, rev 7's E-4, and rev 8's E-5 were all hand-written counts
that disagreed with their own artifact. This closes the class rather than correcting a fourth
instance of it.

### Entry census

| | rev 7 | rev 8 (held) | rev 8 (final) |
|---|---|---|---|
| Entry objects | 59 | 67 | **79** |
| Pinned entries | 51 | 54 | **62** |
| Unpinned entries | 8 | 13 | **17** |
| Vectors carrying ≥1 unpinned entry | 8 | 12 | **16** |

The rev 7 column reproduces Michael Msebenzi's independently reported rev 7 census exactly
(59 / 51 / 8 / 8). The eight vectors added this pass account for the deltas from the held draft:
+12 entries, +4 unpinned, +8 pinned, +4 vectors carrying an unpinned entry.

### How to count root values

**Count 64-hex string values, not `computed` keys.** `differ` and `identical` are booleans, not
roots. Stated explicitly because not stating it is what produced rev 7's E-4.

## Reproduce

**Executed verbatim in a clean directory containing only these three fixture files plus the final
amendments document, before this README's digest was written.**

```
# 1. confirm the generator's pinned rev 8 digest matches the amendments document
grep -o 'rev8_sha256="[a-f0-9]*"' evidence-pinning-fixture-generator-rev8.py
sha256sum evidence-pinning-02-amendments-rev8-2026-09-11.md

# 2. generate
python3 evidence-pinning-fixture-generator-rev8.py > evidence-pinning-fixtures-v2-rev8.json

# 3. cross-check
node evidence-pinning-fixture-crosscheck-rev8.mjs --check evidence-pinning-fixtures-v2-rev8.json
```

Step 1 prints the same 64-hex value twice:
`c42928e6b08f30828d7664f1abcb737431a13cbd19650b64e85b2365cc04636c`.

Step 2 exits 0 and emits a file byte-identical to the shipped
`evidence-pinning-fixtures-v2-rev8.json` — verified with `cmp` in the clean directory. Emission is
deterministic across runs in the same process and across processes.

Step 3 exits 0 and reports:

```
"total_roots_checked": 26,
"roots_checked_raw_children": 24,
"roots_checked_hex_children": 1,
"roots_checked_leaf_raw_digest": 1,
"vectors_in_file": 44,
"mismatches": 0,
"all_agree": true
```

Reference `evidence-pinning-fixtures-v2-rev8.json` sha256:
`b576cb520d0e813e1f792e3d819f8974d8fa2f530745aeeacaf5cdeb50fbf928` — 44,937 bytes, 1,185 lines.

| Artifact | sha256 |
|---|---|
| `evidence-pinning-fixtures-v2-rev8.json` | `b576cb520d0e813e1f792e3d819f8974d8fa2f530745aeeacaf5cdeb50fbf928` |
| `evidence-pinning-fixture-generator-rev8.py` | `519033c9b357f05bc16d1b3477a0c120cfc1475b8e68488db1b096dfd6afdb86` |
| `evidence-pinning-fixture-crosscheck-rev8.mjs` | `310553635ef14b0d2ad2f10e650c5442ad79aeb953da67b3048ba59bbfeb7251` |
| `drafts/evidence-pinning-02-amendments-rev8-2026-09-11.md` | `c42928e6b08f30828d7664f1abcb737431a13cbd19650b64e85b2365cc04636c` |

## The fail paths were exercised, not assumed

A checker that has never failed is not evidence. Each of these was run against a mutated copy of
the final shipped file, this pass, and each exits non-zero with the named message:

| Mutation | Result |
|---|---|
| Restore `pinned_set_empty` on `evi-empty-set-rejects` | exit 1 — `names superseded condition "pinned_set_empty" (rev 8 Finding 38); rev 8 requires "evidence_set_names_no_sources"` |
| Corrupt `evi-root-present-pinned-count-absent-accepted`'s `computed.correct_root` to `ff…ff` | exit 1 — `expected ffff…, got 35bc8fb1…` (the real recomputed root) |
| Set `header.census.malformed` to 19 by hand | exit 1 — `header.census.malformed: file says 19, recomputed 20` |
| **None (shipped file)** | **exit 0, `all_agree: true`, `mismatches: 0`** |

**What this does not test, stated so it is not assumed.** Setting `pinned: true` on
`evi-pinned-absent-rejects`'s entry (defeating the vector's own trigger) still exits 0 — the
cross-check validates roots, census, and condition-identifier hygiene, not whether a vector's input
actually produces the halt its `condition` names. That evaluation is the generator's
`assert_scope_discriminating` (Findings 35–37 only, unchanged from the held draft) plus manual
review of each `expect` string against the amendment text; **it is not automated for Findings 40–46**
and is not claimed to be here.

On the generator side, unchanged from the held draft: swapping `check_entry_identity` and
`set_retrieved_at` for their pinned-only counterparts makes `assert_scope_discriminating` fail the
build with five messages — this is the property the original four rev-8 vectors (Findings 35–37)
exist to have, and it was not re-run this pass because none of the eight new vectors touch that code
path.

## What is verified and what is not

**Verified by cross-language agreement, this pass:**

- All items carried from the held draft (leaf preimage, node/leaf encodings, canonical order,
  distinctness over all of `sources`, bytewise-least set-level `retrieved_at`).
- Every root value in the 44-vector set, including the two new root-bearing vectors
  (`evi-root-present-pinned-count-absent-accepted`, `evi-resolve-all-counts-absent-accepted`),
  recomputed and matched with 0 mismatches.
- Every group count and the entry census, recomputed from the shipped file.
- Superseded-condition rejection, exercised against a real mutation.

**Not verified here:**

- **Any implementation of the rev 8 set**, held or final. No implementer has run it.
- **An independent from-text build of any revision.** See the independence disclosure above.
- **Whether Findings 40–46's eight vectors actually trigger their declared condition** in a real
  verifier. The cross-check does not evaluate this (see "What this does not test" above); it is
  established by the `expect` string and the amendment text, not by an executable assertion.
- Malformed-input handling by any verifier; that is a verifier-side test.
- The `UNKNOWN`, `ADDITIVE`, `COMPLETENESS`, and `RESOLUTION` vectors' resolution logic, which
  describe verifier-side outcomes rather than root computation.
- **Requiredness of `evidence_set_version` and the set-level `retrieved_at`.** Carried from rev 7,
  still open.
- **A pinned entry and an unpinned entry sharing `url` and `retrieved_at`.** Finding 35's text makes
  that pair one retrieval recorded twice, and **no vector covers it.**

## Known limitations carried into this pass

**The condition-enumeration diff.** Fifteen conditions are now named by vectors (up from thirteen in
the held draft) — see the amendments document's "What remains open" for why this is not treated as
closing the diff against Michael's separately reported enumeration count without an actual
name-for-name comparison.

**Thirteen-versus-eleven distinct input shapes**, carried unchanged from the held draft and not
reconciled — see the held draft's own note; the eight new vectors reuse `entry` and `evidence_set`
shapes and add no new one.
