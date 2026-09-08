# evidence-pinning fixtures — v2 preimage, rev 6 rules

**Status: DRAFT. Not filed. Not independent.**

Twenty-nine conformance vectors for the evidence-pinning section of
`draft-krausz-verification-state-02`, computed under `ao-evidence-leaf-v2` with the four-term
canonical order, the rev 5 distinctness rule, and **rev 6's normative node-child encoding**.

## Files

- `evidence-pinning-fixture-generator-rev6.py` — **reference generator.** The sole emitter of
  `evidence-pinning-fixtures-v2-rev6.json`.
- `evidence-pinning-fixture-crosscheck-rev6.mjs` — **Node cross-check.** Recomputes every root
  in the fixture file and diffs. Exits non-zero on any mismatch. Not an emitter.
- `evidence-pinning-fixtures-v2-rev6.json` — the emitted fixture set.

**New filenames per `semantics_change_new_filename.md`.** The generator emits a vector the rev 5
generator did not and moves a field between members; the cross-check verifies two constructions
the rev 5 cross-check skipped. The rev 5 files stay on disk byte-unchanged.

## What changed from the rev 5 set

| Vector | Change | Source |
|---|---|---|
| `evi-node-raw-not-hex` | **NEW.** Two pinned items, concrete root under raw-octet node children, counter-construction root under hex children, the two MUST differ. | rev 6 Finding 27 |
| `evi-root-mismatch-rejects` | `correct_root` moves from `input` to `computed`. Value unchanged. | rev 6 E-3 |

**27 of the 28 shared vectors are byte-identical to rev 5.** The only one that differs is
`evi-root-mismatch-rejects`, and only in which member holds `correct_root`. **No root value in
the set changes.** The new vector's normative root equals the value rev 5 already computed for
the same two-entry set, which confirms Finding 27 pins the branch this side had already taken
rather than altering it.

## Why the new vector exists

Michael Msebenzi's independent implementation, built from the review draft and the amendment
texts alone at `agentoracle-receipt-spec@ac33ad1` (`receipt-verify` `80ca6a6` and `5ffb455`),
agreed with this side on all 28 rev 5 vectors and found that **the interior node's child
encoding was not specified.** Base l.121 gives the node preimage; no sentence in the five texts
said whether `left` and `right` enter as 32 raw octets or as 64 hex characters. Both
implementations chose raw octets without the text compelling it.

A one-item pinned set forms no interior node, so the two readings agree there. Every relational
expectation in the rev 5 set compares two roots computed under the same branch, so those agree
too. **The rev 5 set could not detect the difference.** An implementation choosing hex children
would have passed all 28 vectors.

`evi-node-raw-not-hex` is the smallest set that detects it: two pinned items, one interior node,
a concrete expected root. A hex-children implementation fails it on the value, with no
relational comparison needed.

## Independence disclosure — read before citing

Both `evidence-pinning-fixture-generator-rev6.py` and
`evidence-pinning-fixture-crosscheck-rev6.mjs` were written by the same party. Agreement between
them is a **cross-language check**: it catches language-specific defects (JSON ordering, UTF-8
handling, hash-library differences, integer widths, string comparison rules). It does **not**
establish independence.

**Independence for this section means a build from the specification text alone by a party with
no access to these files.**

**That run has now happened, for the rev 5 set.** Michael Msebenzi built from the review draft
and the amendment texts alone at `ac33ad1`, with his roots committed before any of these files
were opened, and agreed on all 28 vectors. Two limits belong beside that result:

1. **Airlock disclosure.** `evi-root-mismatch-rejects` carried `correct_root` inside `input`,
   which his protocol treats as the permitted side. One concrete normative root was visible to
   him before his roots were fixed. He noticed at extraction, recorded it, did not consult it,
   and his independent recomputation produced the same value. **Rev 6 moves the field to
   `computed`, so no future run needs the disclosure.**
2. **Independence limit.** The node-child encoding was one choice the texts left open, and both
   implementations made it the same way. **The set as run could not have detected a different
   choice.** Rev 6 states the encoding and adds the vector that detects it.

**The rev 6 set has not had an independent run.** Michael has committed to running it the same
day it lands, roots committed before anything of this side's is opened, on the same protocol.
Until then, cross-language agreement here is a cross-language check and nothing more.

Do not describe cross-language agreement in this bundle as independent implementation in any
external message, changelog, deposit, or public artifact.

## Spec bases

Re-derived from `TKCollective/agentoracle-receipt-spec` at HEAD
`ac33ad1dd660ea8473123ab8a3371934255926e9` at build time and compared byte-for-byte against the
local copies. All identical.

| Base | sha256 | bytes | lines |
|---|---|---|---|
| `drafts/evidence-pinning-02-review-draft.md` | `9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096` | 14,469 | 289 |
| `drafts/evidence-pinning-02-amendments-rev5-2026-09-06.md` | `1f901fd7d56fcfe9f858446e5b685b540b5904d6abcfb4b2509e1eb675aa1e51` | 14,631 | 256 |
| `drafts/evidence-pinning-02-amendments-rev6-2026-09-08.md` | `d62ded37dcf63f541e5b670b0cc0f7876e04a182064eb06a32af0037effaf026` | 21,968 | 412 |

## Twenty-nine vectors

- 13 retained from rev 2 (rev 4 "Retained unchanged" list — **rev 4's head at l.402 says "nine";
  thirteen is correct, corrected in rev 6 E-1, and rev 4 is not edited**)
- 8 added by rev 4
- 1 added by rev 5 (`evi-duplicate-bound-tuple-rejects`, Finding 24)
- 6 root-bearing relational vectors — five unchanged from rev 4, one restated under the
  four-term sort (`evi-duplicate-url-distinct-digest`)
- **1 added by rev 6** (`evi-node-raw-not-hex`, Finding 27)

Not emitted: `evi-partial-pinning-honest` and `evi-recompute-claim-inconsistent-rejects`
(removed in rev 2 §8), and `evi-fully-pinned-zero-sources-rejects` (dissolved in rev 4 Finding
18b — unreachable under rev 4 Finding 20's empty-set prohibition).

### Counting by function, and the overlap

| | rev 5 | rev 6 |
|---|---|---|
| Root-bearing vectors | 10 | **12** |
| Root values carried | 19 | **22** |
| `MALFORMED` | 12 | 12 |
| Remaining (`ADDITIVE`, `COMPLETENESS`, `UNKNOWN`, `EMPTY`) | 6 | **5** |

**Under rev 5 these three groups partitioned the set. Under rev 6 they do not.**
`evi-root-mismatch-rejects` is both `MALFORMED` and root-bearing, because the airlock fix moved
its `correct_root` into `computed`. That is a gain — a leaked hint became a real comparison
point — but **12 + 12 + 5 is not a partition of 29**, and any line written about a rev 6 run
must say so rather than present it as one.

## Reproduce

**Build order matters and is one-directional.** The generator pins rev 6's digest, so rev 6 must
be final before the fixture is generated. Editing rev 6 afterwards leaves the pin stale and the
fixture must be regenerated.

```
# 1. confirm the generator's pinned rev 6 digest matches the file
grep -o 'rev6_sha256="[a-f0-9]*"' evidence-pinning-fixture-generator-rev6.py
sha256sum evidence-pinning-02-amendments-rev6-2026-09-08.md

# 2. generate
python3 evidence-pinning-fixture-generator-rev6.py > evidence-pinning-fixtures-v2-rev6.json

# 3. cross-check
node evidence-pinning-fixture-crosscheck-rev6.mjs --check evidence-pinning-fixtures-v2-rev6.json
```

Expected cross-check result: `"all_agree": true`, `"mismatches": 0`,
`"total_roots_checked": 22`.

**Last run of this pair reported 22 root computations checked — 20 under raw-octet children, 1
under the hex-children counter-construction, 1 under the leaf-level raw-digest
counter-construction — with zero mismatches across 29 vectors.**

Reference `evidence-pinning-fixtures-v2-rev6.json` sha256:
`81cfd1bbb6e1f1a55e5ad8eebfeb78addef7465c14f6bd9f4dde8de7a224d9d9`.

### Note on the rev 5 README's digest

The rev 5 README's Reproduce section gave
`fe8567bd734602838c0f70bdc0741e506ff5476207bc641ff77ba3a5ea68e5cc` as the fixture digest. That
was the file at `ac33ad1^`; a header-only change after the digest was written moved the hash, and
at `ac33ad1` the rev 5 fixture hashes to
`5d499bd01f44bd6e0f12b3617c7f104a214555b57a6c80280f5ceb358409b587`. No root was affected, but
the rev 5 bundle could not verify itself through its own Reproduce section. Recorded as rev 6
E-2. This README's digest was written after the fixture was generated, and the Reproduce block
above regenerates it.

## What is verified and what is not

**Verified by cross-language agreement:**

- Leaf preimage: `ao-evidence-leaf-v2` prefix, four members, `0x00` separators, UTF-8 bytes of
  `url`, hex-form of the digest, `content_kind`, `retrieved_at`.
- **Interior node child encoding: raw 32 octets, per rev 6 Finding 27 — and the hex-children
  counter-construction is computed and shown to differ.** New in rev 6; the rev 5 pair verified
  the node prefix but not the child encoding, because neither implementation questioned it.
- **Leaf-level raw-digest counter-construction.** The rev 5 cross-check skipped
  `non_normative_raw_root`, leaving one value the fixture asserted that no implementation
  verified. The rev 6 cross-check computes it.
- Canonical order: four-term bytewise UTF-8 sort.
- Odd-node promotion: promoted unchanged, not duplicated.
- Distinctness: two entries identical across all four bound members are rejected.

**Not verified here:**

- **Independent implementation of the rev 6 set.** The rev 5 set has had one; rev 6 has not.
- Malformed-input handling by any verifier. These vectors carry the wrong-shape input and the
  expected halt; testing that a verifier halts is a verifier-side test, outside the scope of
  this fixture set.
- The UNKNOWN, ADDITIVE and COMPLETENESS vectors, which describe verifier-side resolutions
  rather than root values.
- **Requiredness of `evidence_set_version` and the set-level `retrieved_at`.** Base l.68–76
  marks both required; all nine `evidence_set` inputs omit them. Michael scoped his step (a) to
  the internal consistency of what a set declares and checked requiredness nowhere. This is a
  fixture-versus-text disagreement rather than an ambiguity — one of the two is wrong — and it is
  open for rev 7.

## Known limitation carried into rev 7

**Eleven distinct input shapes across the set, one of them prose-valued.** From Michael's
report: a consumer needs a hand-written branch per vector, and his did. One shape with the
variation carried in named members would make the set runnable by something not told about it in
advance. `"receipt_shape": "no evidence_set member present"` in particular cannot be acted on by
a parser.

**Deferred to rev 7 and named rather than left to drift.** Unifying eleven shapes touches every
vector's input and every consumer's parser; doing it in the same revision as Finding 27 would
make the node-encoding fix wait on a mechanical refactor. Finding 27 is what an implementer needs
in order to not be wrong; the shape unification is what a runner needs in order to be convenient.
