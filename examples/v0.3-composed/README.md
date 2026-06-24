# `verification.v0.3+composed` — conformance fixtures (Phase 1)

Two-signer composed envelope. AgentOracle (`v_gate`) and AgentTrust
(`v_gate_skill`) co-sign a single JWS general serialization over one canonical
payload. Phase 2 adds Presidio (`screen_ref`) as an additive third signer
without altering this suite.

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
payload-{001..004}.json  — accept-vector payloads (pre-JCS object form)
jws-{001..004}.json      — accept-vector JWS general serializations
payload-r{01..03}.json   — reject-vector payloads
jws-r{01..03}.json       — reject-vector JWS general serializations
jwks-agentoracle.json    — Ed25519 public key (kid ao-fixture-v0.3-composed-2026-06)
jwks-agenttrust.json     — Ed25519 public key (kid at-fixture-v0.3-composed-2026-06)
```

## Coverage

### Accept vectors (must verify end-to-end)

| ID       | Scenario                                                                           | composed_decision | Trail |
|----------|------------------------------------------------------------------------------------|-------------------|-------|
| comp-001 | Both issuers approve. No trail anchor.                                             | `act`             | absent |
| comp-002 | AgentOracle approves, AgentTrust halts on skill — composed halts.                  | `halt`            | absent |
| comp-003 | AgentOracle halts on gate, AgentTrust approves — composed halts.                   | `halt`            | absent |
| comp-004 | Both approve and `mycelium_trail_id` resolves — trail is present as a string.      | `act`             | present |

### Reject vectors (must fail for the stated reason)

| ID       | Failure mode                                                | `expected_failure`                |
|----------|-------------------------------------------------------------|-----------------------------------|
| comp-r01 | AgentTrust signature tampered after the fact                | `signature_invalid`               |
| comp-r02 | `"mycelium_trail_id": null` in the payload (grammar break)  | `mycelium_trail_id_is_null`       |
| comp-r03 | Signed `composed_decision` disagrees with AND_PRESENT recompute | `composed_decision_rule_violated` |

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
PASS: 7 vectors (4 accept verified end-to-end, 3 reject correctly refused)
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

| Aspect                          | Phase 1 (this suite)               | Phase 2 (follow-on PR)                                |
|---------------------------------|------------------------------------|--------------------------------------------------------|
| Signers                         | AgentOracle, AgentTrust            | + Presidio                                            |
| Sibling pointers                | `v_gate`, `v_gate_skill`, (`mycelium_trail_id`) | + `screen_ref`                              |
| `action-ref` scope tokens       | Single value per segment           | Lexicographically sorted, comma-joined (vstantch rule) |
| `signing-trust-ref-v1` adoption | Acknowledged                       | Normative                                             |
| Decision rule                   | `AND_PRESENT`                      | `AND_PRESENT` (unchanged)                             |

Vector IDs, kids, and mapping hashes carry forward unchanged into Phase 2.
