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
| `composition-ref-allow.json` | `72acbe4e38fcabf8` | `act` |
| `composition-ref-halt.json` | `d9b73c7dd21e2c2a` | `halt` |

**Hash format:** SHA-256 over **JCS canonical JSON (RFC 8785)** of the full composition_ref object, first 16 hex characters. This is the authoritative format per [@Liuyanfeng1234's clarification](https://github.com/microsoft/autogen/issues/7353) in the AAR thread on June 10. The pipe-separated `raw` string described in [argentum-core#10](https://github.com/giskard09/argentum-core/issues/10) predates the JCS migration and is no longer authoritative; `CompositionRefBuilder` serializes via JCS and hashes the canonical bytes.

JCS implementation used: [`canonicalize`](https://www.npmjs.com/package/canonicalize) (RFC 8785 reference).

### Stable inputs (identical across both fixtures except for the three verdict-distinguishing fields)

| Field | Value |
| --- | --- |
| `delegation_ref` | `ao_delegation_v03_demo_01` |
| `revocation_ref` | `ao_revocation_v03_demo_01` |
| `key_source` | `inline` |
| `authority_verified_at_ms` | `1717804800000` (2026-06-08T00:00:00Z) |
| `revocation_check_at_ms` | `1717804800500` |
| `scope` | `verification:factual_claim:pre_publish` |
| `version` | `composition-ref-v1.0` |
| `composition_built_at_ms` | `1717804801000` |
| `action_ref` (allow fixture) | `ao_action_allow_v03_demo_01` |
| `action_ref` (halt fixture) | `ao_action_halt_v03_demo_01` |

The two fixtures differ only in: `action_ref` and `metadata.domain_verdicts[0].{verdict, gate, receipt_jws}`. Same canonical claim, same standard, same standard_hash, same reviewer key — flipping only `v_adversarial_result` upstream in the AgentOracle receipt drives the entire downstream divergence.

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
AAR fixtures written (JCS mode):
  composition-ref-allow.json  composition_ref = 72acbe4e38fcabf8  (v_gate=act)
  composition-ref-halt.json   composition_ref = d9b73c7dd21e2c2a  (v_gate=halt)

Hash algorithm: SHA-256 over JCS canonical JSON (RFC 8785), first 16 hex chars
JCS implementation: canonicalize@npm (reference)
```

If your `CompositionRefBuilder` produces the same two 16-char hashes from the same input fields, the integration is hash-stable across two independent implementations — which is what makes the field set worth standardizing.

## Open items resolved (in-thread, June 10)

@Liuyanfeng1234 confirmed three open items during the AAR thread exchange:

1. **Canonicalization.** JCS canonical JSON (RFC 8785) over the full field set, not the pipe-separated raw string. Implementation here uses the `canonicalize` npm package as the reference JCS implementation.
2. **Empty optional fields.** Omitted entirely from the JCS object (consistent with RFC 8785).
3. **`domain_verdicts` array ordering.** Insertion-ordered; the issuer determines the order. First verdict carries the primary decision. Consistent with the mapping-verdict pair ordering in `draft-krausz-verification-state`.

## Remaining items pending CompositionRefBuilder confirmation

Three fields where this fixture made best-guess canonical values and is awaiting confirmation:

- **`version` value.** Used `composition-ref-v1.0`. If CompositionRefBuilder expects a different canonical form, the resulting hashes will diverge and we converge on a value.
- **`scope` value.** Used `verification:factual_claim:pre_publish` per giskard09's per-action-intent definition. If a different canonical form is expected (e.g. URN), flag and converge.
- **Composition timestamp field name.** Used `composition_built_at_ms` for the composition-time timestamp (the `ts` element from the legacy pipe format). If CompositionRefBuilder names this field differently in the JCS object, that's a guaranteed hash mismatch source.

## Cross-references

- IETF Internet-Draft: [draft-krausz-verification-state-00](https://datatracker.ietf.org/doc/draft-krausz-verification-state/)
- AgentOracle v0.3 receipt spec: [TKCollective/agentoracle-receipt-spec](https://github.com/TKCollective/agentoracle-receipt-spec/tree/v0.3-binary-halt)
- AgentOracle v0.3 base fixtures: [`../`](..)
- argentum-core composition-ref field def: [giskard09/argentum-core#10](https://github.com/giskard09/argentum-core/issues/10)
- AAR discussion thread: [microsoft/autogen#7353](https://github.com/microsoft/autogen/issues/7353)
- Conforming implementations table: [agentoracle-receipt-spec §8](https://github.com/TKCollective/agentoracle-receipt-spec#8-conforming-implementations)
