# v0.3 Fixture Pair

Minimal, offline-verifiable example pair for [ADR-002](../../adr/ADR-002-canonical-derived-version-binding.md): canonical recommendation, derived gate, versioned mapping binding.

Both fixtures are signed by a **static fixture key** included in this directory (`jwks-fixture.json`). The fixture key is **not** the production AgentOracle signing key — it exists only to let anyone verify these files offline with no network call.

## Files

| File | Purpose |
| --- | --- |
| `canonical-input.json` | Shared canonical input both receipts derive from. Same claim, same context, same scope. |
| `receipt-allow.jws` | Signed v0.3 receipt with `v_gate = "act"`. |
| `receipt-halt.jws` | Signed v0.3 receipt with `v_gate = "halt"`. |
| `jwks-fixture.json` | Static Ed25519 public key for offline verification. **Fixture only — not production.** |
| `verify-fixture.mjs` | Reference offline verifier that exercises the full ADR-002 protocol. |
| `build-fixtures.mjs` | Deterministic regenerator. Run if you want to inspect signing logic. |

## Pinned mapping

Both receipts bind to mapping identifier:

```
v_gate_mapping       = "v0.3.0-2026-05-30"
v_gate_mapping_hash  = "sha256-02d91ee4e9f92efbb6a7218d13f726f400bf48bed79d7e4050e4ee8cd98bc0c1"
```

The mapping document itself lives at [`mappings/v0.3.0-2026-05-30.md`](../../mappings/v0.3.0-2026-05-30.md) and is immutable after publication.

## What the pair demonstrates

The two receipts share **every** canonical input except `v_adversarial_result`. Under mapping `v0.3.0-2026-05-30`:

| Field | `receipt-allow.jws` | `receipt-halt.jws` |
| --- | --- | --- |
| `v_verdict` | `supported` | `supported` |
| `v_confidence` | `0.91` | `0.91` |
| `v_gate_threshold` | `0.70` | `0.70` |
| `v_adversarial_result` | `resilient` | `vulnerable` |
| `v_recommendation` *(derived, signed)* | `confident_supported` | `vulnerable_supported` |
| `v_gate` *(derived, signed)* | **`act`** | **`halt`** |

A verifier holding either receipt:

1. Verifies the JWS signature against `jwks-fixture.json`.
2. Recomputes `v_recommendation` locally from the four signed primitives.
3. Asserts the recomputed value equals the signed `v_recommendation`.
4. Recomputes `v_gate` from `v_recommendation` under the named mapping.
5. Asserts the recomputed value equals the signed `v_gate`.

No relying party ever trusts the issuer's runtime to have applied the mapping correctly. The signature binds the inputs, the outputs, and the mapping identifier together. Any mismatch is a malformed receipt and MUST be treated as `halt`.

## Run the verifier

```bash
cd examples
npm install jose   # one-time
node v0.3/verify-fixture.mjs
```

Expected output:

```
=== v0.3 fixture verification ===
  receipt-allow.jws
    signature:        VALID (kid=ao-fixture-2026-06-v03-ed25519)
    v_recommendation: confident_supported  (recomputed match)
    v_gate:           act                  (recomputed match)
    v_gate_mapping:   v0.3.0-2026-05-30
  receipt-halt.jws
    signature:        VALID (kid=ao-fixture-2026-06-v03-ed25519)
    v_recommendation: vulnerable_supported (recomputed match)
    v_gate:           halt                 (recomputed match)
    v_gate_mapping:   v0.3.0-2026-05-30
=== ALL FIXTURES VERIFIED OK ===
```

## Cross-references

- IETF Internet-Draft: [`draft-krausz-verification-state-00`](https://datatracker.ietf.org/doc/draft-krausz-verification-state/)
- Reference verifier: [`TKCollective/agentoracle-receipt-verify`](https://github.com/TKCollective/agentoracle-receipt-verify)
- Mapping document: [`mappings/v0.3.0-2026-05-30.md`](../../mappings/v0.3.0-2026-05-30.md)
- Architectural decision: [`adr/ADR-002`](../../adr/ADR-002-canonical-derived-version-binding.md)

## Status

These fixtures are intended as a stable reference for partner implementations writing or consuming v0.3 receipts. The canonical inputs, mapping ID, and mapping hash are pinned; if you cite them in another spec or doc, cite this commit hash.
