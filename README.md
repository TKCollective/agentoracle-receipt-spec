# AgentOracle Verification Receipt Format — Draft v0.1

> **Status:** EARLY DRAFT for public discussion. Not yet implemented.
> Posted in response to a [Coinbase Developer Discord #x402 thread](https://discord.gg/cdp) on Apr 29, 2026 about pre-action verification as a sibling family to environment-state attestations.
> Comments / PRs / forks welcome.

This document specifies a **cryptographically signed receipt format** for output from `POST https://agentoracle.co/evaluate` — AgentOracle's pre-action factual claim verification endpoint.

The receipt is designed to be:

1. **Verifiable offline** via published JWKS — consumers don't need to call AgentOracle to confirm a receipt is genuine.
2. **Multi-axis fresh** — signature, calibration, and evidence each have independent `valid_until` timestamps. A claim's underlying evidence can age out without invalidating the calibration of the verifier; the signing key can rotate without invalidating prior receipts.
3. **W3C VC Confidence Method-aligned** ([Oct 2025 WD](https://www.w3.org/TR/vc-confidence-method/)) — confidence as a sidecar property, not a peer claim.
4. **Composable** with the [Decixa](https://decixa.ai) `trust_evidence` axes (uptime / schema / data quality) and with Mastercard Verifiable Intent's `environment.*` constraint family as a sibling under `verification.*`.

---

## 1. Background and Motivation

Today AgentOracle's `/evaluate` returns:

```json
{
  "evaluation_id": "eval_1777474288985_2voiqu",
  "evaluation": {
    "overall_confidence": 0.87,
    "recommendation": "act",
    "recommendation_text": "Safe to act. Claim is well-supported by multiple sources.",
    "claims": [...]
  },
  "meta": { "endpoint": "/evaluate", "verification_method": "...", ... }
}
```

That's adequate for **online**, **trusted-channel** consumers — they call AgentOracle directly, get the verdict, act on it. The `evaluation_id` works as an audit-trail-by-lookup identifier when a downstream consumer needs to revisit what was checked.

It is **not adequate** for:

- **Offline verification** — an auditor reviewing a 6-month-old agent decision cannot independently verify the verdict was actually issued by AgentOracle without trusting our database.
- **Receipt-passing protocols** — e.g. when an agent presents proof-of-verification to a downstream verifier (Decixa's resolver, an x402 facilitator, Mastercard's Verifiable Intent mandate, an end-user agent governance dashboard) without a roundtrip to AgentOracle.
- **Multi-axis freshness reasoning** — the consumer cannot tell *why* a stale receipt is stale: did the signing key rotate, did the calibration anchor refresh, or did the underlying evidence move? Each has different remediation.

This spec proposes a JWS-signed receipt with separate `valid_until` per axis to address all three.

---

## 2. Architectural Position

This format places AgentOracle's verification output in the **`verification.*` family** rather than under [Mastercard Verifiable Intent's](https://github.com/mastercard/verifiable-intent) existing `environment.*` constraint family.

Justification (per the architectural critique raised in the [linked Discord thread](https://discord.gg/cdp)):

| Property | `environment.*` (existing) | `verification.*` (proposed) |
|---|---|---|
| Predicate type | Boolean (e.g. `market_state == OPEN`) | Probabilistic in `[0,1]` (e.g. `confidence == 0.87`) |
| Threshold ownership | Oracle-defined (semantics fixed) | Verifier-defined (consumer policy) |
| Freshness | Uniform single TTL | Multi-axis (signature × calibration × evidence) |
| Gating logic | Verifier-trivial (`if !state then halt`) | Verifier-substantive (`if confidence < user_threshold then halt`) |

Adopting `verification.*` as a sibling family preserves the clean fail-closed semantics of `environment.*` while accommodating the inherently probabilistic shape of factual claim verification. Aligns with the [W3C VC Confidence Method](https://www.w3.org/TR/vc-confidence-method/) precedent of treating confidence as a sidecar property.

---

## 3. Receipt Envelope

The receipt is a **JWS** ([RFC 7515](https://datatracker.ietf.org/doc/html/rfc7515)) compact serialization, alternative encodings (JWS JSON, COSE) MAY be supported in future revisions.

### 3.1 JWS Header

```json
{
  "alg": "ES256",
  "kid": "ao-2026-04-key-01",
  "typ": "ao-receipt+jws"
}
```

| Field | Required | Notes |
|---|---|---|
| `alg` | yes | `ES256` initial draft. Other curves under consideration. |
| `kid` | yes | Resolves via JWKS at `https://agentoracle.co/.well-known/jwks.json` |
| `typ` | yes | Fixed `"ao-receipt+jws"` |

### 3.2 JWS Payload (Claims)

```json
{
  "iss": "https://agentoracle.co",
  "sub": "urn:agentoracle:evaluation:eval_1777474288985_2voiqu",
  "iat": 1777474288,
  "exp": 1785250288,
  "ao_v": "v0.1",
  "ao_claim": {
    "text": "The Eiffel Tower is in Paris, France.",
    "hash": "sha256:9b1c6...",
    "redacted": false
  },
  "ao_verdict": "supported",
  "ao_confidence": 0.87,
  "ao_method": "agentoracle/v2-adversarial-fever-calibrated",
  "ao_calibration": {
    "anchor_dataset": "FEVER-1.0-paper_dev-200",
    "anchor_seed": 42,
    "anchor_as_of": "2026-04-21",
    "valid_until": 1793026288
  },
  "ao_sources_used": ["sonar", "sonar-pro", "adversarial", "gemma"],
  "ao_evidence": {
    "uri": "https://agentoracle.co/evaluate/eval_1777474288985_2voiqu/evidence",
    "valid_until": 1777560688
  }
}
```

#### 3.2.1 Standard JWT claims

| Claim | Required | Notes |
|---|---|---|
| `iss` | yes | Always `https://agentoracle.co` |
| `sub` | yes | URN form of the original `evaluation_id` |
| `iat` | yes | Receipt signing time (Unix seconds) |
| `exp` | yes | Signature validity end. Tied to JWK rotation cadence (proposed: 90 days). |

#### 3.2.2 AgentOracle-namespaced claims

| Claim | Required | Notes |
|---|---|---|
| `ao_v` | yes | Receipt format version. This document = `v0.1`. |
| `ao_claim` | yes | The verified claim — `text` OR `hash` (claim text is OPTIONAL when caller marks the input as PII-sensitive; the hash is then the binding object) |
| `ao_verdict` | yes | One of `supported` / `refuted` / `unverifiable` |
| `ao_confidence` | yes | Float in `[0,1]` |
| `ao_method` | yes | Self-describing method tag identifying the verification pipeline + calibration anchor |
| `ao_calibration` | yes | Calibration evidence — see §3.2.3 |
| `ao_sources_used` | yes | Array of source labels actually used in this evaluation (subset of `["sonar","sonar-pro","adversarial","gemma"]`) |
| `ao_evidence` | optional | Pointer to per-claim source set (recoverable via authenticated GET) |

#### 3.2.3 Calibration claim

The `ao_calibration` claim is the cornerstone of the multi-axis freshness model.

```json
{
  "anchor_dataset": "FEVER-1.0-paper_dev-200",
  "anchor_seed": 42,
  "anchor_as_of": "2026-04-21",
  "valid_until": 1793026288
}
```

Each calibration anchor identifies a publicly-reproducible benchmark used to calibrate AgentOracle's confidence scores. **The anchor is itself an audit object** — given `anchor_dataset`, `anchor_seed`, and `anchor_as_of`, anyone can replay the benchmark and verify the confidence calibration.

`valid_until` for calibration is **independent of the signature `exp`**. Recalibration on a new dataset (e.g., switching to FEVER 2.0 adversarial or Symmetric) extends or replaces the calibration anchor without forcing reissuance of every receipt signed under the prior anchor.

Reference: AgentOracle's current calibration anchor is the open benchmark at [github.com/TKCollective/agentoracle-fever-benchmark](https://github.com/TKCollective/agentoracle-fever-benchmark).

#### 3.2.4 Evidence claim

The `ao_evidence` claim points at the per-claim source set used during verification. The URI is RECOMMENDED to be authenticated (e.g., served only with proof of `sub` ownership) since source URLs may include data the original caller treated as sensitive context.

`ao_evidence.valid_until` reflects the TTL of the underlying source set itself. Web sources move; cached source content may go stale. This timestamp tells the consumer when the *evidence* — not the *signature* and not the *calibration* — should be re-fetched.

---

## 4. JWKS

AgentOracle SHALL publish a JWKS at:

```
https://agentoracle.co/.well-known/jwks.json
```

containing all currently-active signing keys plus the most recent N rotated keys (proposed: N=4, i.e. 1 year of rotation history at quarterly cadence).

Example:

```json
{
  "keys": [
    {
      "kty": "EC",
      "crv": "P-256",
      "kid": "ao-2026-04-key-01",
      "x": "...",
      "y": "...",
      "alg": "ES256",
      "use": "sig"
    },
    {
      "kty": "EC",
      "crv": "P-256",
      "kid": "ao-2026-01-key-01",
      "x": "...",
      "y": "...",
      "alg": "ES256",
      "use": "sig"
    }
  ]
}
```

Rotation cadence: proposed 90 days, key history retained for verification of older receipts.

---

## 5. Multi-Axis Freshness Verification

A consumer verifying a receipt MUST evaluate three axes independently:

### 5.1 Signature Freshness

```
SIGNATURE_FRESH(receipt) ==
  receipt.kid IN jwks.keys AND
  jwks.keys[receipt.kid].active_until > now AND
  receipt.iat <= now AND
  receipt.exp > now
```

### 5.2 Calibration Freshness

```
CALIBRATION_FRESH(receipt) ==
  receipt.ao_calibration.valid_until > now
```

### 5.3 Evidence Freshness

```
EVIDENCE_FRESH(receipt) ==
  receipt.ao_evidence.valid_until > now
```

### 5.4 Consumer Policy

The receipt is **VERIFIED VALID** iff `SIGNATURE_FRESH(r)` is true. Consumers MAY require additional axes based on their policy:

- **Lightweight consumer** (fast-decision agent): require only `SIGNATURE_FRESH`.
- **Standards-track consumer** (Mastercard mandate, x402 facilitator): require `SIGNATURE_FRESH AND CALIBRATION_FRESH`.
- **Auditor consumer** (regulator, legal review): require all three.

**Gating logic is owned by the consumer, not the oracle.** AgentOracle publishes axis-level timestamps; consumer policy decides which axes are mandatory.

---

## 6. Composability

### 6.1 With Decixa `trust_evidence`

Decixa's `trust_evidence` composite ([as documented](https://www.decixa.ai/docs)) currently spans:
- **Schema Compliance** (does the response conform to declared `payment_requirements`?)
- **Uptime + Latency**
- **Data Quality** (currently reserved slot)

AgentOracle receipts are designed to feed the **Data Quality** axis. The `ao_confidence` field is the candidate signal, with `ao_calibration` providing the audit grounds. Decixa's composite scoring may consume signed receipts directly without trusting AgentOracle's runtime to compute the input — receipts are independently verifiable.

### 6.2 With Mastercard Verifiable Intent

Per the architectural argument that surfaced in the [Coinbase Developer Discord #x402 thread](https://discord.gg/cdp), `verification.*` is proposed as a **sibling family** to Mastercard's existing `environment.*` constraint family in the [Verifiable Intent repository](https://github.com/mastercard/verifiable-intent).

A user-issued mandate declaring a `verification.factual_claim_state` constraint would carry a confidence threshold and reference an issuer set (e.g. `[https://agentoracle.co]`). At gating time, the mandate-evaluator validates: (1) signature freshness, (2) confidence ≥ user threshold, (3) calibration freshness against the user's policy.

---

## 7. Open Questions

The following items are intentionally underspecified pending discussion:

1. **COSE encoding** — should the spec include a normative COSE binding alongside JWS for embedded-device consumers?
2. **Multi-issuer receipts** — when verification spans multiple oracles (e.g. AgentOracle + a different content authenticity verifier), should the receipt support multi-signature attestation, or should consumers verify N separate single-signer receipts?
3. **Calibration anchor versioning** — when the underlying benchmark dataset itself revises (FEVER 1.0 → 2.0), how do we name and reference both versions without breaking existing consumers?
4. **Evidence URI authentication** — proposed: caller's bearer presentation matches `sub`. Alternative: signed evidence URI that delegates access for a TTL.
5. **Privacy** — when `ao_claim.redacted == true`, the `text` field is omitted and only `hash` is present. Does this provide adequate privacy guarantees for content-team consumers verifying brand-sensitive claims pre-publication?

---

## 8. Status, Contribution, and Discussion

This is a **DRAFT**. Nothing here is implemented yet. The point of publishing this draft is to invite collaboration before code lands.

- Issues / discussion: [GitHub issues on this repo](https://github.com/TKCollective/agentoracle-receipt-spec/issues)
- Discord: [#x402 on Coinbase Developer Discord](https://discord.gg/cdp)
- Email: hello@agentoracle.co

PRs and forks welcome. Particularly interested in:
- Alignment review from anyone on the [Mastercard Verifiable Intent](https://github.com/mastercard/verifiable-intent) team
- Implementation feedback from the [W3C VC Confidence Method](https://www.w3.org/TR/vc-confidence-method/) editors
- Composability review from the [Decixa](https://decixa.ai) team

---

## Acknowledgements

This draft is a direct response to the architectural critique raised by Beenz / [headlessoracle](https://github.com/headlessoracle) in the Coinbase Developer Discord #x402 thread (Apr 29, 2026). The objection that factual claim verification's predicate shape doesn't fit the existing `environment.*` namespace is the originating insight. The Path B proposal (sibling family with confidence as sidecar) is theirs.

Acknowledgement is not endorsement — they have not reviewed this draft.

---

## License

Spec text: [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/). Reference implementations (forthcoming): MIT.
