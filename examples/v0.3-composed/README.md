# `verification.v0.3+composed` — conformance fixtures (Phase 1 + Phase 2)

Composed envelope, up to three co-signers over one canonical payload (JWS
general serialization). AgentOracle (`v_gate`) and AgentTrust (`v_gate_skill`)
are the Phase 1 base; **Phase 2 adds Presidio (`screen_ref`)** as an additive
third sibling pointer + signature. The Phase 1 vectors (`comp-001..004`,
`comp-r01..r03`) are unchanged byte-for-byte — Phase 2 only appends. `screen_ref`
is an `action-ref-v1` content address over a PII-screening verdict whose block
carries its four-field preimage, so verifiers recompute the `action_ref` rather
than trust it; the three Phase 2 `screen_ref` preimages are byte-identical to
argentum-core conformance vectors `presidio-x402-003/004/005`.

Spec references:
- `../../README.md` — Mycelium Trails section, sibling-pointer model
- IETF `draft-krausz-verification-state-01` — envelope grammar, AND_PRESENT rule
- giskard09/argentum-core — `signing-trust-ref-v1`, `mycelium-provider-protocol`

## What's in here

```
build_fixtures.py        — regenerate everything from scratch (writes keys,
                           payloads, signatures, vectors.json)
verify.mjs               — Node.js stdlib verifier (node:crypto + vendored JCS)
verify.py                — Python stdlib + cryptography sibling verifier
vectors.json             — suite manifest (accept + reject vectors, expected
                           canonical SHA-256, signer kids, composition flags)
payload-{001..007}.json  — accept-vector payloads (pre-JCS object form);
                           005..007 carry the Phase 2 screen_ref leg
jws-{001..007}.json      — accept-vector JWS general serializations
                           (005..007 are three-signer)
payload-r{01..04}.json   — reject-vector payloads (r04 = screen_ref mismatch)
jws-r{01..04}.json       — reject-vector JWS general serializations
jwks-agentoracle.json    — Ed25519 public key (kid ao-fixture-v0.3-composed-2026-06)
jwks-agenttrust.json     — Ed25519 public key (kid at-fixture-v0.3-composed-2026-06)
jwks-presidio.json       — Ed25519 public key (kid presidio-fixture-v0.3-composed-2026-06)
```

## Coverage

### Accept vectors (must verify end-to-end)

| ID       | Scenario                                                                           | composed_decision | Trail |
|----------|------------------------------------------------------------------------------------|-------------------|-------|
| comp-001 | Both issuers approve. No trail anchor.                                             | `act`             | absent |
| comp-002 | AgentOracle approves, AgentTrust halts on skill — composed halts.                  | `halt`            | absent |
| comp-003 | AgentOracle halts on gate, AgentTrust approves — composed halts.                   | `halt`            | absent |
| comp-004 | Both approve and `mycelium_trail_id` resolves — trail is present as a string.      | `act`             | present |
| comp-005 | Three-signer: AO + AT + Presidio `PII_REDACTED` screen, all act (= `presidio-x402-003`). | `act`        | absent |
| comp-006 | Three-signer: AO + AT approve, Presidio `PII_BLOCKED` screen is the decisive halt (= `presidio-x402-004`). | `halt` | absent |
| comp-007 | Three-signer: AO + AT + Presidio `clean-allow` screen, all act (= `presidio-x402-005`). | `act`         | absent |

### Reject vectors (must fail for the stated reason)

| ID       | Failure mode                                                | `expected_failure`                |
|----------|-------------------------------------------------------------|-----------------------------------|
| comp-r01 | AgentTrust signature tampered after the fact                | `signature_invalid`               |
| comp-r02 | `"mycelium_trail_id": null` in the payload (grammar break)  | `mycelium_trail_id_is_null`       |
| comp-r03 | Signed `composed_decision` disagrees with AND_PRESENT recompute | `composed_decision_rule_violated` |
| comp-r04 | `screen_ref.action_ref` ≠ `action-ref-v1` recompute of its preimage | `screen_ref_action_ref_mismatch` |

## Two-receipt composition framing

A composed envelope is the only signed object — there are not two separate
receipts being aggregated by a downstream client. Each issuer signs the same
canonical payload using their own kid. Adding Presidio in Phase 2 is purely
additive:

1. The `screen_ref` sibling pointer is populated.
2. A third entry is appended to `jws.signatures`.
3. The AND_PRESENT recompute now folds in the screen verdict.

No grammar break for existing verifiers — fields they don't recognize are
ignored under the standard JWS general serialization rules, and signature
verification continues to require every present `kid` to validate.

## Composition rule — `AND_PRESENT`

```
verdicts = [v.verdict for v in (v_gate, v_gate_skill, screen_ref) if v is not None]
composed_decision = "act" if verdicts and all(v == "act" for v in verdicts) else "halt"
```

Absent sibling pointers do not contribute. Any present-and-halt collapses the
composed decision to halt. Empty composition (no signers) fails closed.

## `mycelium_trail_id` grammar

When the Mycelium Provider `/external/trail` call fails or is not invoked, the
field MUST be **absent** from the payload — never `null`. Verifiers reject the
envelope on encountering `null`. When the call succeeds, the field is a string
identifier extracted from the trail manifest.

## Running the verifiers

```sh
# Node (verify.mjs)
node verify.mjs

# Python (verify.py)
python3 verify.py
```

Both must print byte-identical output:

```
PASS: 11 vectors (7 accept verified end-to-end, 4 reject correctly refused)
```

The two implementations are intentionally independent recomputations — Node
uses `node:crypto` with a vendored RFC 8785 (JCS) serializer; Python uses
`cryptography.hazmat.primitives.asymmetric.ed25519` with its own JCS port. A
parity pass means the canonical bytes, AND_PRESENT outcomes, and Ed25519
signature checks all agree across two language runtimes.

## Regenerating

```sh
python3 build_fixtures.py
```

This writes fresh Ed25519 keypairs (private keys held only in
`/tmp/...-priv-*.pem` during the run, not committed), re-canonicalizes every
payload, re-signs both JWS heads, and rewrites `vectors.json` with the new
`expected_canonical_sha256` digests.

## Phase 1 vs Phase 2

Both phases now ship in this suite; Phase 2 is purely additive on the byte-stable
Phase 1 base.

| Aspect                          | Phase 1 (`comp-001..004`, `r01..r03`) | Phase 2 (`comp-005..007`, `r04`)                       |
|---------------------------------|------------------------------------|--------------------------------------------------------|
| Signers                         | AgentOracle, AgentTrust            | + Presidio                                            |
| Sibling pointers                | `v_gate`, `v_gate_skill`, (`mycelium_trail_id`) | + `screen_ref`                              |
| `action-ref` scope tokens       | Single value per segment           | Lexicographically sorted, comma-joined, no spaces (action-ref.md @16dbc92) |
| `signing-trust-ref-v1`          | Acknowledged                       | Pointer present (`multi_party` / `str-003`)            |
| `screen_ref` recompute          | n/a                                | Verifier recomputes `action_ref` from preimage (`r04`) |
| Decision rule                   | `AND_PRESENT`                      | `AND_PRESENT` (unchanged, now folds `screen_ref`)      |

Phase 1 vector IDs, kids, and mapping hashes are unchanged byte-for-byte.
