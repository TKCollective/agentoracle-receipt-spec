# evidence-pinning fixtures — v2 preimage, rev 5 rules

**Status: DRAFT. Not filed. Not independent.**

Twenty-eight conformance vectors for the evidence-pinning section of
`draft-krausz-verification-state-02`, computed under `ao-evidence-leaf-v2` with
the four-term canonical order and the rev 5 distinctness rule.

## Files

- `evidence-pinning-fixture-generator.py` — **reference generator.** The sole emitter of
  `evidence-pinning-fixtures-v2-rev5.json`.
- `evidence-pinning-fixture-crosscheck.mjs` — **Node cross-check.** Recomputes every root in
  `evidence-pinning-fixtures-v2-rev5.json` and diffs. Exits non-zero on any mismatch. Not an emitter.
- `evidence-pinning-fixtures-v2-rev5.json` — the emitted fixture set.

## Independence disclosure — read before citing

Both `evidence-pinning-fixture-generator.py` and `evidence-pinning-fixture-crosscheck.mjs` were written by the same
party. Agreement between them is a **cross-language check**: it catches
language-specific defects (JSON ordering, UTF-8 handling, hash-library
differences, integer widths, string comparison rules). It does **not** establish
independence.

**Independence for this section means a build from the specification text alone
by a party with no access to these files.** For evidence-pinning that is Michael
Beenz or Pablo, both of whom have working evidence-pinning implementations
derived from the drafts alone. Neither has yet been asked to reproduce this
fixture set; the second-implementation confirmation the section requires is
still outstanding, and is the pre-filing blocker.

Do not describe cross-language agreement here as independent implementation in
any external message, changelog, deposit, or public artifact.

## Spec bases

Re-derived from `TKCollective/agentoracle-receipt-spec` at HEAD
`49b7d039576b17e39dd707c9f223de5670c9be86` and compared byte-for-byte against
the local copies. Both identical.

| Base | sha256 | bytes | lines |
|---|---|---|---|
| `drafts/evidence-pinning-02-review-draft.md` | `9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096` | 14,469 | 289 |
| `drafts/evidence-pinning-02-amendments-rev5-2026-09-06.md` | `1f901fd7d56fcfe9f858446e5b685b540b5904d6abcfb4b2509e1eb675aa1e51` | 14,631 | 256 |

## Twenty-eight vectors, reconciled against the rev 5 ledger

- 13 retained from rev 2 (rev 4 "Retained unchanged" list)
- 8 added by rev 4
- 1 added by rev 5 (`evi-duplicate-bound-tuple-rejects`, Finding 24)
- 6 root-bearing relational vectors — five unchanged from rev 4, one restated
  under the four-term sort (`evi-duplicate-url-distinct-digest`)

Not emitted: `evi-partial-pinning-honest` and `evi-recompute-claim-inconsistent-rejects`
(removed in rev 2 §8), and `evi-fully-pinned-zero-sources-rejects` (dissolved in
rev 4 Finding 18b — unreachable under rev 4 Finding 20's empty-set prohibition).

## Reproduce

```
python3 evidence-pinning-fixture-generator.py > evidence-pinning-fixtures-v2-rev5.json
node evidence-pinning-fixture-crosscheck.mjs --check evidence-pinning-fixtures-v2-rev5.json
```

Expected result of the cross-check: `"all_agree": true`, `"mismatches": 0`. Last
run of this pair reported 18 root computations checked, zero mismatches.
Reference `evidence-pinning-fixtures-v2-rev5.json` sha256: `fe8567bd734602838c0f70bdc0741e506ff5476207bc641ff77ba3a5ea68e5cc`.

## What is verified and what is not

**Verified by cross-language agreement:**

- Leaf preimage: `ao-evidence-leaf-v2` prefix, four members, `0x00` separators,
  UTF-8 bytes of `url`, hex-form of the digest, `content_kind`, `retrieved_at`.
- Interior node: `ao-evidence-node-v1` prefix, unchanged.
- Canonical order: four-term bytewise UTF-8 sort.
- Odd-node promotion: promoted unchanged, not duplicated.
- Distinctness: two entries identical across all four bound members are rejected
  by `checkDistinct`.

**Not verified here:**

- Independent implementation. Cross-language agreement is not independence.
- Malformed-input handling by any verifier. These vectors carry the wrong-shape
  input and the expected halt; testing that a verifier halts is a verifier-side
  test, outside the scope of this fixture set.
- The UNKNOWN and ADDITIVE vectors, which describe verifier-side resolutions
  rather than root values.
