# AAR Integration — composition_ref wrapping AgentOracle v0.3 receipt

This directory shows AgentOracle's v0.3 JWS receipts embedded inside argentum-core's `composition_ref.metadata.domain_verdicts` array, per the integration shape outlined by [@Liuyanfeng1234 in microsoft/autogen#7353](https://github.com/microsoft/autogen/issues/7353).

The goal is a **two-implementer hash-match interop test**: AgentOracle produces these composition_refs; the AAR/argentum-core implementation runs the same inputs through `CompositionRefBuilder` and confirms the 16-char hashes match.

## Files

| File | Purpose |
| --- | --- |
| `composition-ref-allow.json` | composition_ref wrapping an ACT receipt (`v_recommendation = confident_supported`, `v_gate = act`) |
| `composition-ref-halt.json` | composition_ref wrapping a HALT receipt (`v_recommendation = vulnerable_supported`, `v_gate = halt`) |
| `build-aar-fixtures.mjs` | Deterministic regenerator. Reproduces both files byte-for-byte. |

## Computed composition_ref hashes (for comparison)

| Fixture | composition_ref | v_gate |
| --- | --- | --- |
| `composition-ref-allow.json` | `8dc585dea3364832` | `act` |
| `composition-ref-halt.json` | `0eb7a736df8bc85c` | `halt` |

These were computed using the exact format from [argentum-core#10](https://github.com/giskard09/argentum-core/issues/10):

```
raw = "action:{action_ref}|delegation:{delegation_ref}|revocation:{revocation_ref}|meta:{json(metadata)}|key_src:{key_source}|auth_ts:{ms}|revoke_ts:{ms}|ts:{ms}"
composition_ref = SHA-256(raw).hexdigest()[:16]
```

with these stable inputs (identical across both fixtures except for `metadata.domain_verdicts[0].verdict` / `gate` / `receipt_jws`):

| Field | Value |
| --- | --- |
| `delegation_ref` | `ao_delegation_v03_demo_01` |
| `revocation_ref` | `ao_revocation_v03_demo_01` |
| `key_source` | `inline` |
| `authority_verified_at_ms` | `1717804800000` (2026-06-08T00:00:00Z) |
| `revocation_check_at_ms` | `1717804800500` |
| `ts_ms` | `1717804801000` |
| `action_ref` (allow) | `ao_action_allow_v03_demo_01` |
| `action_ref` (halt) | `ao_action_halt_v03_demo_01` |

> **Canonical metadata JSON convention:** keys sorted, no whitespace, UTF-8. This matches the convention typically applied to the `json(metadata)` slot in the pipe-separated `raw` string. If `CompositionRefBuilder` uses a different canonicalization for the metadata embedding, please flag it — that's the first place a hash mismatch will surface.

## Field mapping — AgentOracle v0.3 ↔ AAR domain_verdicts

| `domain_verdicts[i]` field | Source in AgentOracle receipt |
| --- | --- |
| `claim_id` | `subject.claim_hash` from canonical-input |
| `verdict` | `v_recommendation` (signed in JWS payload) |
| `gate` | `v_gate` (signed in JWS payload) |
| `standard` | `v_gate_mapping` (signed) |
| `standard_hash` | `v_gate_mapping_hash` (signed, content-addressed) |
| `reviewer.jws_signer_kid` | JWS protected header `kid` |
| `reviewer.jwks_uri` | `signature_meta.jwks_url` |
| `reviewer.receipt_typ` | JWS protected header `typ` |
| `receipt_jws` | Full Flattened JWS (verifiable offline against [`../jwks-fixture.json`](../jwks-fixture.json)) |

The mapping is direct: every `domain_verdicts` field has a one-to-one source in the signed AgentOracle receipt envelope. An auditor holding `composition-ref-{allow,halt}.json` and the JWKS fixture can:

1. Verify `composition_ref` by recomputing the SHA-256 from the same fields
2. Verify `receipt_jws` signature against the AgentOracle JWKS (offline, no network call)
3. Recompute `verdict` from the signed receipt's `v_verdict / v_confidence / v_adversarial_result / v_gate_threshold` per mapping `v0.3.0-2026-05-30`
4. Recompute `gate` from `verdict` under that mapping
5. Assert all four (`composition_ref` hash, JWS signature, recomputed verdict, recomputed gate) match the embedded values

No relying party trusts either issuer's runtime.

## Pinned mapping

```
v_gate_mapping       = "v0.3.0-2026-05-30"
v_gate_mapping_hash  = "sha256-02d91ee4e9f92efbb6a7218d13f726f400bf48bed79d7e4050e4ee8cd98bc0c1"
```

This is the same mapping referenced in [`../canonical-input.json`](../canonical-input.json) and the v0.3 reference receipts.

## Reproduce

```bash
cd /path/to/agentoracle-receipt-spec/examples
npm install jose   # one-time, if not already
cd v0.3/integrations/aar
node build-aar-fixtures.mjs
```

Expected output:

```
AAR fixtures written:
  composition-ref-allow.json  composition_ref = 8dc585dea3364832  (v_gate=act)
  composition-ref-halt.json   composition_ref = 0eb7a736df8bc85c  (v_gate=halt)
```

If your `CompositionRefBuilder` produces the same two 16-char hashes from the same input fields, the integration is hash-stable across two independent implementations — which is what makes the field set worth standardizing.

## Open items for cross-reference review

A small number of field-level questions worth flagging back to argentum-core#10 before locking the integration:

1. **Metadata canonicalization convention.** Is `json(metadata)` in the `raw` string assumed to be RFC 8785 JCS, or sorted-keys/no-whitespace (the convention used here)? Both are deterministic; they differ on Unicode escape behavior for non-ASCII strings.
2. **Empty optional fields.** When `delegation_ref` or `revocation_ref` are absent, is the slot omitted from `raw` or set to an empty string (`delegation:|`)? This fixture sets demo values so it doesn't hit this case, but a real auditor will.
3. **Multiple verdicts.** `domain_verdicts` is an array; for the multi-standard case (e.g. EU AI Act Article 12 + FDA SaMD evaluated against the same claim), does the array order need to be canonical? Sort by `standard`? By insertion order? Affects hash stability.

These are the only edge cases that surfaced while building the fixture; everything else maps cleanly.

## Cross-references

- IETF Internet-Draft: [draft-krausz-verification-state-00](https://datatracker.ietf.org/doc/draft-krausz-verification-state/)
- AgentOracle v0.3 receipt spec: [TKCollective/agentoracle-receipt-spec](https://github.com/TKCollective/agentoracle-receipt-spec/tree/v0.3-binary-halt)
- AgentOracle v0.3 base fixtures: [`../`](..)
- argentum-core composition-ref field def: [giskard09/argentum-core#10](https://github.com/giskard09/argentum-core/issues/10)
- AAR discussion thread: [microsoft/autogen#7353](https://github.com/microsoft/autogen/issues/7353)
- Conforming implementations table: [agentoracle-receipt-spec §8](https://github.com/TKCollective/agentoracle-receipt-spec#8-conforming-implementations)
