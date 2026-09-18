# evidence-pinning fixtures — v2 preimage, rev 8 rules

**Status: DRAFT. Not filed. Not independent. HELD — rev 8 is not final.**

Thirty-six conformance vectors for the evidence-pinning section of
`draft-krausz-verification-state-02`, computed under `ao-evidence-leaf-v2` with the four-term
canonical order, the rev 5 distinctness rule, rev 6's normative node-child encoding, rev 7's
`condition` members and non-disclosing identifiers, and **rev 8's whole-of-`sources` scope rules**.

**Why HELD.** Rev 8 rules three of seven all-versus-pinned scope choices Michael Msebenzi reported
in this text; five are outstanding and will be ruled in this same revision rather than a later one.
This bundle is complete and self-verifying as it stands, but the vector count and the condition
vocabulary can still move before rev 8 is cut. **Do not treat these filenames or digests as final,
and do not run a conformance claim against them yet.**

## Files

- `evidence-pinning-fixture-generator-rev8.py` — **reference generator.** The sole emitter of
  `evidence-pinning-fixtures-v2-rev8.json`.
- `evidence-pinning-fixture-crosscheck-rev8.mjs` — **Node cross-check.** Recomputes every root in
  the fixture file, recomputes the census, re-derives each new vector's scope discrimination, and
  rejects superseded condition identifiers. Exits non-zero on any mismatch. Not an emitter.
- `evidence-pinning-fixtures-v2-rev8.json` — the emitted fixture set.

**New filenames per `semantics_change_new_filename.md`.** Two rules move from a pinned-only reading
to a whole-of-`sources` reading, two condition identifiers are renamed, and four vectors are added
that a rev 7-conformant implementation holding the pinned-only reading **passes today and fails
here**. The rev 7 files stay on disk byte-unchanged.

## What changed from the rev 7 set

| Vector | Change | Source |
|---|---|---|
| `evi-duplicate-unpinned-entries-rejects` | **NEW.** Two unpinned entries, same `url` and `retrieved_at`, differing only in `unpinned_reason`. `MALFORMED`, `duplicate_bound_tuple`. | rev 8 Finding 35 |
| `evi-unpinned-retrieved-at-noncanonical-rejects` | **NEW.** Non-canonical `retrieved_at` on the unpinned entry of a mixed set. `MALFORMED`, `retrieved_at_not_canonical_form`. | rev 8 Finding 37 |
| `evi-set-retrieved-at-equals-unpinned-value` | **NEW.** Set-level `retrieved_at` equal to the unpinned entry's earlier value. **Accepted**, root-bearing, designation `SET SCOPE`. | rev 8 Finding 36 |
| `evi-set-retrieved-at-above-unpinned-value-rejects` | **NEW.** Same two entries, set-level value taken from the pinned entry. `MALFORMED`, `set_retrieved_at_not_bytewise_least`. | rev 8 Finding 36 |
| `evi-empty-set-rejects` | `condition` renamed `pinned_set_empty` → `evidence_set_names_no_sources`. Input and root unchanged. | rev 8 Finding 38 |
| `evi-set-retrieved-at-not-earliest-rejects` | `condition` renamed `set_retrieved_at_not_first_in_canonical_order` → `set_retrieved_at_not_bytewise_least`. Input and root unchanged. | rev 8 Finding 38 |

**All 32 rev 7 vectors are retained, and 30 of them are byte-identical.** The only changes to
existing vectors are the two renamed `condition` values, on `evi-empty-set-rejects` and
`evi-set-retrieved-at-not-earliest-rejects`; no input, designation, `expect` string or root moves.
**No root value in the set changes** — rev 7's 23 root values are preserved byte-identically under
unchanged `(vector id, key)` pairs and the one new root-bearing vector adds the 24th. Verified by
diffing the two emitted sets rather than by inspection of the patch.

**One naming item this revision does not act on.** `evi-set-retrieved-at-not-earliest-rejects` still
says "not-earliest" in its identifier, while rev 6 replaced "earliest" with a bytewise basis and
Finding 36 keeps it. The identifier describes the input configuration, so Finding 34 is satisfied,
but it describes it in superseded vocabulary. **Named as a candidate for the reserved findings
rather than renamed here**, because renaming a vector id changes the surface a consumer keys on and
belongs in the same revision as the remaining five scope choices.

## Why the four new vectors exist

Michael Msebenzi's implementation reads the entry-identity rule and the set-level `retrieved_at`
rule over the full `sources` array. Pablo Play, from the same text, read the entry-identity rule
over the pinned subset only. **Both pass all 32 rev 7 vectors.**

That is verifiable in the rev 7 file rather than taken on report: its only duplicate pair is two
pinned entries, its only non-canonical `retrieved_at` is on a pinned entry, and its one set-level
`retrieved_at` comparison has every entry pinned. **The rev 7 set could not detect the
difference**, exactly as the rev 5 set could not detect the node-child encoding.

The four new vectors are the smallest set that detects it, and the build **proves** that rather
than asserting it. `assert_scope_discriminating` in the generator, and the matching block in the
cross-check, evaluate each new vector's own input under both readings and fail if the two agree.
Run against a generator holding the pinned-only reading, the build fails with five messages; run
against the shipped set, it passes. Two of the four turn on a halt, one turns on an **accept**, and
the accept/reject pair means no implementation passes both limbs by mixing domains.

## Independence disclosure — read before citing

Both `evidence-pinning-fixture-generator-rev8.py` and `evidence-pinning-fixture-crosscheck-rev8.mjs`
were written by the same party. Agreement between them is a **cross-language check**: it catches
language-specific defects (JSON ordering, UTF-8 handling, hash-library differences, integer widths,
string comparison rules). It does **not** establish independence.

**Independence for this section means a build from the specification text alone by a party with no
access to these files.**

**No revision of this section has had one in that sense.** Michael Msebenzi's rev 5 run was
independent; his rev 6 and rev 7 runs extended that implementation rather than rebuilding from
text, so they are **confirmed-by-extension**. Pablo Play's from-text reconstruction is the filing
gate for -02 and has not landed. The rev 8 set has had **no** implementer run of any kind.

Do not describe cross-language agreement in this bundle as independent implementation in any
external message, changelog, deposit, or public artifact.

### Rev 8 Finding 39 — the uniqueness assertion is withdrawn

Rev 7's generator and cross-check asserted that no two vectors name the same condition. That was
true of the rev 7 set by accident of construction and was never a stated rule. **Three of the four
new vectors deliberately inject an already-vectored condition on a different entry class**, because
injecting the same condition from a different direction is how a scope rule gets covered.

The assertion is withdrawn and replaced: every `MALFORMED` vector still names exactly one
condition, a condition may be named by more than one vector, and **no vector may name a superseded
identifier**. Rev 7's Finding 33 itself is unchanged.

### Superseded condition identifiers

Published rather than dropped, so a reader comparing a rev 7 run against a rev 8 run can map the
reported value. Shipped in `header.superseded_conditions`:

| superseded identifier (rev 7) | identifier (rev 8) |
|---|---|
| `pinned_set_empty` | `evidence_set_names_no_sources` |
| `set_retrieved_at_not_first_in_canonical_order` | `set_retrieved_at_not_bytewise_least` |

Both the generator and the cross-check **fail the build** if any vector names a superseded
identifier. A future rename adds a row; it never silently replaces a value.

## Spec bases

Re-derived from `TKCollective/agentoracle-receipt-spec` at
`3d0ec0e82229c1336340f0323d54904e5baf38b2` and compared byte-for-byte against the local copies.
All identical.

| Base | sha256 | bytes | lines |
|---|---|---|---|
| `drafts/evidence-pinning-02-review-draft.md` | `9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096` | 14,469 | 289 |
| `drafts/evidence-pinning-02-amendments-rev2-2026-09-04.md` | `a957802a4ed4d5a4097e2066fd0be4cbc5bf5d777ebbd5809e47f3bd4637bf74` | 24,470 | 378 |
| `drafts/evidence-pinning-02-amendments-rev3-2026-09-04.md` | `d770436219038098d1ea8c9dad08b96d7939eec5207de8556138ffe500dc1216` | 9,313 | 162 |
| `drafts/evidence-pinning-02-amendments-rev4-2026-09-06.md` | `060fc52c067b5d7da5a57d3ea6ef32e05aa0417bc4b1abd9fdf0f9f9faed731c` | 28,914 | 463 |
| `drafts/evidence-pinning-02-amendments-rev5-2026-09-06.md` | `1f901fd7d56fcfe9f858446e5b685b540b5904d6abcfb4b2509e1eb675aa1e51` | 14,631 | 256 |
| `drafts/evidence-pinning-02-amendments-rev6-2026-09-08.md` | `d62ded37dcf63f541e5b670b0cc0f7876e04a182064eb06a32af0037effaf026` | 21,968 | 412 |
| `drafts/evidence-pinning-02-amendments-rev7-2026-09-09.md` | `6b13f6fc35d745c2642edcb52a2754f7cd43340ded3248b5d1ba70a431d6c037` | 17,732 | 296 |
| `drafts/evidence-pinning-02-amendments-rev8-2026-09-11.md` | `a92c17e8240d8aaccd3ac1d74119a8ddb3095624eb677c914ee208168f5e961a` | 26,159 | 390 |

The rev 8 digest is pinned in the generator as `rev8_sha256` and emitted in `header.spec_bases`.
**The pin is one-directional: rev 8 must be final before the fixture is generated, and editing rev
8 afterwards leaves the pin stale and requires regeneration.** The Reproduce block below checks the
pin against the file as its first step, so a stale pin is caught rather than shipped.

## Thirty-six vectors

- 13 retained from rev 2
- 8 added by rev 4
- 1 added by rev 5 (`evi-duplicate-bound-tuple-rejects`, Finding 24)
- 6 root-bearing relational vectors
- 1 added by rev 6 (`evi-node-child-encoding`, Finding 27 — renamed in rev 7 Finding 34)
- 3 added by rev 7 (Findings 33a, 33b, 33c)
- **4 added by rev 8** (Findings 35, 36, 37)

Not emitted: `evi-partial-pinning-honest` and `evi-recompute-claim-inconsistent-rejects` (removed in
rev 2 §8), and `evi-fully-pinned-zero-sources-rejects` (dissolved in rev 4 Finding 18b).

### Counting by function, and the overlap

| | rev 5 | rev 6 | rev 7 | rev 8 |
|---|---|---|---|---|
| Total vectors | 28 | 29 | 32 | **36** |
| Root-bearing vectors | 10 | 12 | 13 | **14** |
| Root values carried | 19 | 22 | 23 | **24** |
| `MALFORMED` | 12 | 12 | 13 | **16** |
| Remaining (`ADDITIVE`, `COMPLETENESS`, `UNKNOWN`, `EMPTY`, `RESOLUTION`) | 6 | 6 | 7 | 7 |
| Overlap (`MALFORMED` **and** root-bearing) | 0 | 1 | 1 | 1 |
| Distinct conditions named | — | — | 13 | 13 |

> **14 + 16 + 7 − 1 = 36.**

The overlap is still `evi-root-mismatch-rejects` alone. `SET SCOPE` is a new designation and its one
vector is root-bearing, so `Remaining` does not move. Distinct conditions stay at thirteen because
three of the four new vectors reuse a condition (Finding 39).

**No count in this bundle is written by hand.** Every group count, the vector total, and the entry
census are derived by equality from the emitted set at build time (`census()` in the generator,
emitted as `header.census`), and the cross-check recomputes all of them from the shipped file and
fails on any disagreement. Rev 6's E-1, rev 7's E-4, and rev 8's E-5 were all hand-written counts
that disagreed with their own artifact. This closes the class rather than correcting a fourth
instance of it.

### Entry census

Derived by the same walker, and stated because it is the evidence for "the rev 7 set could not
fail":

| | rev 7 | rev 8 |
|---|---|---|
| Entry objects | 59 | **67** |
| Pinned entries | 51 | **54** |
| Unpinned entries | 8 | **13** |
| Vectors carrying ≥1 unpinned entry | 8 | **12** |

The rev 7 column is this side's walker run over `evidence-pinning-fixtures-v2-rev7.json`, and it
**reproduces Michael Msebenzi's independently reported rev 7 census exactly** — 59 / 51 / 8 / 8.
The four new vectors account for the deltas: +5 unpinned, +3 pinned, +8 entries, +4 vectors.

### How to count root values

**Count 64-hex string values, not `computed` keys.** `differ` and `identical` are booleans, not
roots. Stated explicitly because not stating it is what produced rev 7's E-4.

## Reproduce

**Executed verbatim in a clean directory containing only these four files, before this README's
digest was written.** Rev 6's E-2 and rev 8's E-7 were both README digests that did not match the
file they described; running the block is the only remedy that holds.

```
# 1. confirm the generator's pinned rev 8 digest matches the file
grep -o 'rev8_sha256="[a-f0-9]*"' evidence-pinning-fixture-generator-rev8.py
sha256sum evidence-pinning-02-amendments-rev8-2026-09-11.md

# 2. generate
python3 evidence-pinning-fixture-generator-rev8.py > evidence-pinning-fixtures-v2-rev8.json

# 3. cross-check
node evidence-pinning-fixture-crosscheck-rev8.mjs --check evidence-pinning-fixtures-v2-rev8.json
```

Step 1 prints the same 64-hex value twice:
`a92c17e8240d8aaccd3ac1d74119a8ddb3095624eb677c914ee208168f5e961a`.

Step 2 exits 0 and emits a file byte-identical to the shipped
`evidence-pinning-fixtures-v2-rev8.json` — verified with `cmp` in the clean directory. Emission is
deterministic across runs in the same process and across processes.

Step 3 exits 0 and reports:

```
"total_roots_checked": 24,
"roots_checked_raw_children": 22,
"roots_checked_hex_children": 1,
"roots_checked_leaf_raw_digest": 1,
"vectors_in_file": 36,
"mismatches": 0,
"all_agree": true
```

Reference `evidence-pinning-fixtures-v2-rev8.json` sha256:
`b7e4e33b241b4bed94613d5d15d02bc259b43824d320f961ef35c991a999a075` — 38,055 bytes, 1,013 lines.

| Artifact | sha256 |
|---|---|
| `evidence-pinning-fixtures-v2-rev8.json` | `b7e4e33b241b4bed94613d5d15d02bc259b43824d320f961ef35c991a999a075` |
| `evidence-pinning-fixture-generator-rev8.py` | `8e2693bc8467906b5a9973e976bfed3e15a69ea58fe4a50e6e473a553c2ed55f` |
| `evidence-pinning-fixture-crosscheck-rev8.mjs` | `310553635ef14b0d2ad2f10e650c5442ad79aeb953da67b3048ba59bbfeb7251` |

### Note on the rev 7 README's digest

`evidence-pinning-fixture-README-rev7.md` l.220–221 gives the rev 7 fixture digest as
`81cfd1bb…`; the shipped file hashes `a8679bdf5acb56ed7cd614086c5ea44438bcd6735b356e88c5e40172e8c696f1`,
both on disk and at `3d0ec0e`. Its Reproduce block also runs the **rev 6** filenames and states rev
6's expected figures (22 roots across 29 vectors); the rev 7 pair actually reports **23 roots
checked — 21 raw / 1 hex / 1 leaf — across 32 vectors**, verified by running it. Recorded as rev 8
E-7. **Rev 7 is not edited.**

## The fail paths were exercised, not assumed

A checker that has never failed is not evidence. Each of these was run against a mutated copy of
the shipped file, and each exits non-zero with the named message:

| Mutation | Result |
|---|---|
| Restore `pinned_set_empty` on `evi-empty-set-rejects` | halts — names superseded condition |
| Make the duplicate unpinned pair differ in `url` | halts — identity rule does not halt |
| Move the accept limb's set-level `retrieved_at` to the pinned value | halts — 2 mismatches, both readings |
| Make the non-canonical `retrieved_at` canonical | halts — no non-canonical value present |
| Change `header.census.malformed` from 16 to 15 | halts — recomputed 16 |
| Corrupt one `evidence_root` value | halts — expected/got diff |
| **None (shipped file)** | **exit 0, `all_agree: true`** |

And on the generator side: swapping `check_entry_identity` and `set_retrieved_at` for their
pinned-only counterparts makes `assert_scope_discriminating` fail the build with five messages,
which is the property the four new vectors exist to have.

## What is verified and what is not

**Verified by cross-language agreement:**

- Leaf preimage: `ao-evidence-leaf-v2` prefix, four members, `0x00` separators.
- Interior node child encoding: raw 32 octets, per rev 6 Finding 27, with the hex-children
  counter-construction computed and shown to differ.
- Leaf-level raw-digest counter-construction.
- Canonical order: four-term bytewise UTF-8 sort.
- Odd-node promotion: promoted unchanged, not duplicated.
- Distinctness over all of `sources`, pinned and unpinned alike (rev 8 Finding 35).
- Set-level `retrieved_at` as the bytewise-least value in `sources` (rev 8 Finding 36).
- Every group count and the entry census, recomputed from the shipped file.

**Not verified here:**

- **Any implementation of the rev 8 set.** No implementer has run it.
- **An independent from-text build of any revision.** See the independence disclosure above.
- Malformed-input handling by any verifier; that is a verifier-side test.
- The `UNKNOWN`, `ADDITIVE` and `COMPLETENESS` vectors, which describe verifier-side resolutions.
- **Requiredness of `evidence_set_version` and the set-level `retrieved_at`.** Base l.68–76 marks
  both required; the `evidence_set` inputs that predate rev 8 omit them. Carried from rev 7 and
  still open — and rev 8's Finding 36 now gives the set-level member a defined value, which makes
  the omission more visible rather than less.
- **A pinned entry and an unpinned entry sharing `url` and `retrieved_at`.** Finding 35's text makes
  that pair one retrieval recorded twice, and **no vector covers it.** Named rather than left to
  drift; a candidate for the reserved findings.

## Known limitations carried into rev 8

**Thirteen distinct input shapes across the set, one of them prose-valued.** Unchanged from rev 7 and
still deferred: a consumer needs a hand-written branch per vector. The four new vectors use an
existing `evidence_set` shape and add no fourteenth — measured by grouping vectors on the sorted key
set of `input`, which gives **13 for rev 7 and 13 for rev 8**. Michael's rev 7 report put the figure
at eleven; rev 7's README repeated it. The two counts are not reconciled — his may group shapes by
what a parser must branch on rather than by key set — and **the number is his measure to correct,
not this side's to overwrite.** What both agree on is the direction: rev 8 adds none.

**Five scope choices outstanding.** Michael Msebenzi reported seven all-versus-pinned scope choices;
rev 8 rules three. The remaining five are expected to be repaired the same way — state the rule over
`sources` in its own terms — but a presumption is not a ruling, and each needs its own condition
identifier and its own discriminating vector. **The vector count and condition vocabulary here can
still move.**

**The condition-enumeration diff.** Thirteen conditions are named by vectors; Michael puts the
malformed-condition enumeration in the specification text at fifteen. Unaffected by Finding 39,
which changes how many vectors reach a condition and not which conditions exist. Still open.
