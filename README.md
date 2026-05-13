# AgentOracle Verification Receipt Format — Draft v0.2 (in progress)

> **Status:** EARLY DRAFT for public discussion. Not yet implemented.
> Posted in response to a [Coinbase Developer Discord #x402 thread](https://discord.gg/cdp) on Apr 29, 2026 about pre-action verification as a sibling family to environment-state attestations.
> Comments / PRs / forks welcome.

> ⚠️ **Benchmark numbers are provisional — not yet third-party reproducible.**
> The cited FEVER metrics in this document come from two different evaluation settings that are not directly comparable:
> - **93.9% label accuracy** is measured on FEVER 1.0 dev with **oracle evidence supplied** (gold evidence fed to the label classifier).
> - **78.4% FEVER score** is measured on FEVER 1.0 dev with **our retrieval pipeline end-to-end** (our retriever + our label).
>
> Conflating them in a single sentence is our error and will be corrected. In addition, FEVER 1.0 is a public 2018 benchmark — parametric-knowledge contamination on a modern LLM is a live risk that has not yet been controlled for.
>
> Until the eval harness is public and reproducible by a third party, treat these numbers as **provisional**. Planned before any external citation:
> - Publish docker-wrapped, seeded eval harness
> - Report recall@5 and recall@10 on dev alongside headline scores
> - Run contamination-controlled eval on a newer held-out benchmark (AVeriTeC 2024) and publish side-by-side
>
> See [Discord #x402 thread, Apr 29, 2026](https://discord.gg/cdp) for the original critique from @beenz that prompted this disclosure.

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

## 7. Canonicalization (Normative)

> **Status:** New in v0.2. Closes BLOCKER #1 from v0.1 review.

All cryptographic signatures over a receipt's claim set MUST be computed over the **canonical byte representation** of the JWS payload (Section 3.2), not over the producer-emitted serialization. This section specifies exactly which canonicalization rules apply, why, and how implementers and verifiers MUST handle them.

### 7.1 Why canonicalization is required

The JSON Web Signature container ([RFC 7515](https://datatracker.ietf.org/doc/html/rfc7515)) signs whatever bytes the producer emits. JSON itself permits semantically-equivalent but byte-different representations of the same logical value: key order, whitespace, Unicode escape forms, number representation (e.g. `0.94` vs `9.4e-1`), and trailing zeros all vary across JSON serializers.

Without a canonicalization step, a receipt that is byte-different but semantically identical (e.g. re-pretty-printed, key-reordered by a proxy, or round-tripped through a JSON library that emits keys alphabetically) will fail signature verification even though the payload's meaning has not changed. This is a known interoperability hazard in JWS-based receipt formats and has historically broken downstream verifiers in W3C VC, OIDC userinfo, and HTTP message signatures.

v0.1 did not specify canonicalization. **v0.2 makes it normative.**

### 7.2 Canonicalization rules (MUST)

Producers MUST canonicalize the JWS Payload (Section 3.2) per [RFC 8785 — JSON Canonicalization Scheme (JCS)](https://datatracker.ietf.org/doc/html/rfc8785) before signing. Specifically:

1. **Object keys** MUST appear in lexicographic UTF-16 code unit order at every level of nesting. (JCS §3.2.3, computed per RFC 8785 Appendix B.)
2. **Numbers** MUST be serialized per [ECMAScript 2015 §7.1.12.1 (`Number.prototype.toString`)](https://tc39.es/ecma262/2015/#sec-tostring-applied-to-the-number-type), which is the algorithm RFC 8785 incorporates by reference. For example, `0.94` is canonical; `0.940` and `9.4e-1` are not.
3. **Strings** MUST use minimum-form Unicode escapes per RFC 8785 §3.2.2.2: ASCII printable characters appear literally; ASCII control characters and the four mandatory escapes (`\"`, `\\`, `\b`, `\f`, `\n`, `\r`, `\t`) use their short escape form; all other characters appear literally as UTF-8.
4. **Whitespace** MUST be eliminated entirely. The canonical form is a single line with no insignificant whitespace.
5. **Insignificant zero, negative zero, NaN, and infinity** — the canonical form for any zero value (including `-0`) is the seven-bit ASCII character `0` (0x30). `NaN`, `Infinity`, and `-Infinity` are NOT permitted in receipt payloads. Producers MUST reject such values at construction time; verifiers MUST reject receipts that contain them.
6. **Arrays** preserve emission order (JCS does not sort array elements). Receipt producers MUST preserve the semantic order of array fields such as `evidence.sources` and `claims[]`.

### 7.3 What gets canonicalized

The canonicalization applies to **the JWS Payload only** — the JSON object containing the protected claims in Section 3.2. The JWS Protected Header (Section 3.1) is base64url-encoded separately and uses standard JWS rules, not JCS.

The signing input, per [RFC 7515 §5.1 step 5](https://datatracker.ietf.org/doc/html/rfc7515#section-5.1), becomes:

```
BASE64URL(UTF8(JWS Protected Header))
  || '.' ||
BASE64URL(JCS(JWS Payload))
```

Where `JCS(...)` is the canonicalized byte sequence per RFC 8785, and `BASE64URL(...)` is unpadded base64url per [RFC 4648 §5](https://datatracker.ietf.org/doc/html/rfc4648#section-5).

### 7.4 Verifier behavior (MUST)

Receipt verifiers MUST NOT trust the bytes a receipt arrives with directly. The verification algorithm is:

1. Split the compact JWS at the `.` separator into `header_b64`, `payload_b64`, `signature_b64`.
2. Base64url-decode `payload_b64` to recover the original payload bytes.
3. Parse the recovered bytes as JSON.
4. Re-canonicalize the parsed object using JCS rules (Section 7.2).
5. Verify that the re-canonicalized bytes are byte-identical to the bytes from step 2.
6. If step 5 passes, perform JWS signature verification per RFC 7515 §5.2 using the re-canonicalized bytes.
7. If step 5 fails, the receipt MUST be rejected with reason `"non-canonical payload"`. This rejection is independent of and prior to signature validation.

The purpose of step 5 is to ensure that downstream caching layers, JSON reformatters, or buggy proxies cannot strip a receipt's canonical form silently while preserving signature validity — a class of bug that has caused production incidents in OIDC userinfo deployments.

### 7.5 Reference implementations

Producers and verifiers SHOULD use one of the following well-maintained JCS implementations rather than hand-rolling:

- **Node.js / TypeScript:** [`canonicalize` (npm)](https://www.npmjs.com/package/canonicalize). MIT licensed. Maintained by the [openidf/jcs working group](https://github.com/cyberphone).
- **Python:** [`jcs` (PyPI)](https://pypi.org/project/jcs/). MIT licensed.
- **Go:** [`gowebpki/jcs`](https://github.com/gowebpki/jcs). Apache 2.0.
- **Rust:** [`serde_jcs`](https://crates.io/crates/serde_jcs). Apache 2.0.

All four pass the [official RFC 8785 test suite](https://github.com/cyberphone/json-canonicalization/tree/master/testdata).

### 7.6 Worked example

Given a logical payload:

```json
{
  "iss": "https://agentoracle.co",
  "sub": "did:web:agentoracle.co:agents:a8b3",
  "iat": 1762400000,
  "ao_claim": {
    "confidence": 0.94,
    "text": "Bitcoin is currently trading at $67,432"
  }
}
```

The canonical form (single line, no whitespace, keys sorted at every depth) is:

```
{"ao_claim":{"confidence":0.94,"text":"Bitcoin is currently trading at $67,432"},"iat":1762400000,"iss":"https://agentoracle.co","sub":"did:web:agentoracle.co:agents:a8b3"}
```

This is the byte sequence that gets base64url-encoded as the JWS payload and that the signature is computed over. Both producer and verifier MUST arrive at this exact byte sequence regardless of intermediate JSON library behavior.

### 7.7 Migration from v0.1

v0.1 receipts (issued before this section is implemented) used producer-default JSON serialization without JCS. Verifiers SHOULD support a transitional mode that:

- For receipts with `protected.alg == "EdDSA"` and `protected.kid` matching a `kid` issued before the cutover date (announced in CHANGELOG.md), accept the receipt's payload bytes as-issued without canonicalization re-check.
- For receipts issued on or after the cutover date, enforce Section 7.4 strictly.

The cutover date will be announced at least 30 days in advance and recorded in the `transitional_modes` block of the JWKS metadata (Section 8.5).

---

## 8. Key Rotation Policy (Normative)

> **Status:** New in v0.2. Closes BLOCKER #2 from v0.1 review.

Receipt signing keys MUST rotate on a regular cadence. This section specifies the rotation policy and how verifiers reconcile receipts signed with rotated keys.

### 8.1 Rotation cadence (MUST)

Producers MUST rotate their primary signing key at least every **90 days**. Producers SHOULD rotate more frequently if any of the following occur:

- The private key material is suspected of compromise.
- A key custody event (HSM migration, deployment infrastructure change, personnel turnover with key access).
- A cryptographic vulnerability is disclosed against the signing algorithm (currently EdDSA over Curve25519).

For scheduled rotations, producers MUST publish the new key in the JWKS at least **7 days before** activating it for signing.

### 8.2 Overlap window (MUST)

When a key rotates, the predecessor key MUST remain published in the JWKS for at least **90 days** after the rotation. During this overlap window:

- The new key signs all new receipts.
- The old key signs no new receipts.
- Verifiers MUST accept receipts signed by either key, provided the receipt's `iat` (issued-at) timestamp falls within the corresponding key's validity window.

The rationale for a 90-day overlap matches the maximum receipt freshness window for the calibration axis (Section 5.2). Receipts older than the overlap window are eligible for the stale-signature handling specified in Section 5.1, not the rotated-key handling here.

### 8.3 `kid` format and uniqueness (MUST)

Each key MUST have a `kid` (key ID) that is globally unique within the issuer's JWKS and that follows this format:

```
ao-receipt-{YYYY}-{MM}-{algorithm}-{8-hex}
```

Where:
- `YYYY-MM` is the year and month of key generation (not activation).
- `algorithm` is the JOSE algorithm identifier in lowercase (`ed25519` for `EdDSA` over Curve25519).
- `8-hex` is the leading 8 hex characters of the SHA-256 hash of the public key material in raw byte form, providing both uniqueness and a tamper-evident binding between `kid` and key.

Example: `ao-receipt-2026-04-ed25519-f2753b7c`

Verifiers MUST treat the `kid` as an opaque identifier for JWKS lookup. They MUST NOT parse the date components of the `kid` for trust decisions — dates are operational metadata, not security boundaries.

### 8.4 JWKS metadata extensions

In addition to the standard JWKS fields ([RFC 7517](https://datatracker.ietf.org/doc/html/rfc7517)), each key entry MUST include the following AgentOracle-specific metadata fields:

```json
{
  "kty": "OKP",
  "crv": "Ed25519",
  "x": "<base64url public key>",
  "kid": "ao-receipt-2026-04-ed25519-f2753b7c",
  "alg": "EdDSA",
  "use": "sig",
  "agentoracle:activated_at": "2026-04-15T00:00:00Z",
  "agentoracle:deactivated_at": null,
  "agentoracle:expires_at": "2026-10-15T00:00:00Z"
}
```

Where:
- `activated_at` is the UTC timestamp at which this key began signing new receipts.
- `deactivated_at` is `null` while the key is the active signing key; it is set to a UTC timestamp when a successor key takes over signing duty. After `deactivated_at` is set, the key remains in the JWKS for the 90-day overlap window.
- `expires_at` is `activated_at + 180 days` (90-day signing + 90-day overlap). After `expires_at`, the key MAY be removed from the JWKS. Receipts referencing a `kid` no longer in the JWKS MUST be rejected with reason `"key not found in JWKS"`.

The `agentoracle:` namespace prefix is used to avoid collision with any future IANA-registered JWK parameters. If this metadata is later standardized through IANA, the prefix will be dropped in the corresponding version of this spec.

### 8.5 `transitional_modes` block

The JWKS document MUST include a top-level `transitional_modes` block that lists currently-active transition policies, including the v0.1 → v0.2 canonicalization cutover (Section 7.7):

```json
{
  "keys": [ ... ],
  "transitional_modes": {
    "canonicalization": {
      "v0_1_v0_2_cutover": "2026-07-01T00:00:00Z",
      "v0_1_grandfathered_kids": ["ao-receipt-2026-04-ed25519-f2753b7c"]
    }
  }
}
```

Verifiers SHOULD consult `transitional_modes` to determine whether legacy receipts are still acceptable per the migration policies in Sections 7.7 and 5.1.

### 8.6 `kid` resolution algorithm (MUST)

Given a receipt with JWS Protected Header `kid = K`, verifiers MUST resolve `K` to a verification key using exactly this algorithm:

1. Fetch the JWKS from the issuer's `iss + /.well-known/jwks.json` URL.
2. Validate the JWKS document against [RFC 7517 §5](https://datatracker.ietf.org/doc/html/rfc7517#section-5).
3. Search the `keys` array for an entry where `kid == K`. If no entry is found, reject with reason `"key not found in JWKS"`.
4. If the matched entry's `agentoracle:expires_at` is in the past relative to the verifier's current time, reject with reason `"key expired"`.
5. If the receipt's `iat` claim is before the matched entry's `agentoracle:activated_at`, reject with reason `"receipt issued before key activation"`.
6. If the matched entry's `agentoracle:deactivated_at` is non-null AND the receipt's `iat` is after `deactivated_at`, reject with reason `"key was rotated before receipt issuance"`.
7. Use the matched entry's public key material to verify the JWS signature per RFC 7515 §5.2.

Verifiers MUST NOT skip steps 4-6 even if step 7 would succeed. The timestamp checks are independent security boundaries.

### 8.7 Emergency rotation

If a key is compromised or suspected compromised, producers MUST publish an emergency rotation that:

1. Sets the compromised key's `agentoracle:deactivated_at` to the time of suspected compromise (not the time of detection).
2. Adds a new key with `agentoracle:activated_at` equal to the moment of publication.
3. Sets the compromised key's `agentoracle:expires_at` to `agentoracle:deactivated_at + 24 hours` (NOT the standard 90-day overlap).
4. Publishes an entry in `transitional_modes.compromised_keys[]` listing the compromised `kid` and the suspected compromise window.

Receipts signed by the compromised key within the suspected compromise window MAY be retroactively rejected by verifiers consulting the `compromised_keys` list. Receipts signed before the suspected compromise window remain valid, since the key material was sound at signing time.

### 8.8 Worked example: scheduled rotation

| Time (UTC) | Action | Active signing kid | JWKS contents |
|---|---|---|---|
| 2026-04-15T00:00Z | v0.1 launch | `ao-receipt-2026-04-ed25519-f2753b7c` | [f27…] |
| 2026-07-01T00:00Z | New kid published 7d before activation | `ao-receipt-2026-04-ed25519-f2753b7c` | [f27…, 9d8…] |
| 2026-07-08T00:00Z | Rotation: 9d8 takes over | `ao-receipt-2026-07-ed25519-9d8a4e1f` | [f27… (deactivated_at set), 9d8…] |
| 2026-10-06T00:00Z | f27 expires (90d overlap) | `ao-receipt-2026-07-ed25519-9d8a4e1f` | [9d8…] |

### 8.9 Migration from v0.1 single-key model

v0.1 used a single fixed `kid` (`ao-receipt-2026-04-ed25519-f2753b7c`) with no rotation policy. The first scheduled rotation under v0.2 SHALL be implemented within 30 days of v0.2 spec finalization. The legacy v0.1 `kid` will be carried forward as the first-generation key under the new rotation policy, with `agentoracle:activated_at` backfilled to the original key generation date.

---

## 9. Replay Protection (Normative)

> **Status:** New in v0.2. Closes BLOCKER #3 from v0.1 review.

A cryptographically-signed receipt is meaningless if a malicious consumer can present the same receipt repeatedly to bypass a downstream policy that requires fresh verification. This section specifies how verifiers detect and reject replayed receipts, and how producers cooperate to make replay detection deterministic.

### 9.1 Why replay protection is required

Receipts are bearer artifacts — anyone who possesses a valid receipt can present it to a downstream verifier. Without replay protection, an agent could re-present a single "act" receipt to repeatedly bypass policy checks long after the original underlying claim has staled. This is structurally analogous to OAuth bearer-token replay and is mitigated using the same primitives: per-receipt nonces, an anchored issuance window, and verifier-side seen-nonce tracking.

v0.1 did not specify replay protection. **v0.2 makes it normative.**

### 9.2 Receipt-side fields (MUST)

The JWS Payload (Section 3.2) MUST include the following additional namespaced claims:

```json
{
  "ao_nonce": "01926b48-7a3c-7000-8000-1f5e6c7d8a90",
  "ao_chain": {
    "prev": "sha256:c4e1a82b...",
    "seq": 47829
  },
  "ao_anchor": {
    "settle_tx": "0x296c8d905621310c67c335ff47a8391af58149df6f1511c348de4290472b817a",
    "settle_chain": "eip155:8453",
    "settle_log_index": 2
  }
}
```

| Claim | Required | Notes |
|---|---|---|
| `ao_nonce` | yes | [UUIDv7](https://datatracker.ietf.org/doc/html/rfc9562#section-5.7) — a 128-bit identifier that is unique per receipt and embeds the issuance timestamp in its leading bits. Producers MUST NOT reuse a nonce. Verifiers use this as the primary anti-replay key. |
| `ao_chain.prev` | yes (after first receipt) | The SHA-256 hash (lowercase hex, `sha256:`-prefixed) of the canonical JCS bytes of the immediately preceding receipt issued by the same `kid`. The first receipt issued by a given `kid` SHALL set `prev` to the special sentinel `sha256:0000000000000000000000000000000000000000000000000000000000000000`. |
| `ao_chain.seq` | yes | Monotonically increasing 64-bit unsigned integer, scoped to the issuing `kid`. The first receipt issued by a `kid` MUST have `seq: 0`. Each subsequent receipt MUST have `seq` equal to the predecessor's `seq + 1`. |
| `ao_anchor.settle_tx` | optional, see §9.5 | When the receipt is generated in the same request that triggered an x402 settle, this field MUST be populated with the on-chain transaction hash. Provides an independent secondary anti-replay key tied to chain finality. |
| `ao_anchor.settle_chain` | optional, see §9.5 | [CAIP-2](https://chainagnostic.org/CAIPs/caip-2) chain identifier matching the settle network. |
| `ao_anchor.settle_log_index` | optional, see §9.5 | Log index of the USDC Transfer event within the settle transaction. Disambiguates multi-settle transactions. |

### 9.3 Verifier behavior (MUST)

Receipt verifiers MUST maintain a **seen-nonce cache** with the following properties:

1. **Default retention window:** at least 7 days (matches the longest practical inter-receipt observation gap for human-audit workflows). Verifiers MAY extend this for audit-grade consumers.
2. **Storage form:** any structure that supports O(1) membership testing — a Redis SET, a SQLite UNIQUE INDEX, a probabilistic Bloom filter sized for the verifier's traffic, or an in-process LRU. Implementation choice is verifier-side.
3. **Lookup key:** the tuple `(iss, kid, ao_nonce)`. The issuer + kid scoping prevents accidental collision between different issuers' nonce spaces.

The verification algorithm extends Section 8.6 (`kid` resolution) with the following additional steps performed AFTER signature verification succeeds:

1. Compute the lookup key `(receipt.iss, receipt.protected.kid, receipt.payload.ao_nonce)`.
2. If the lookup key is already present in the seen-nonce cache, reject the receipt with reason `"replay detected: nonce previously seen"`.
3. If `ao_anchor.settle_tx` is present, query the corresponding chain for transaction inclusion. If the settle transaction has not been mined on `ao_anchor.settle_chain`, reject with reason `"settle anchor not finalized"`. Verifiers MAY skip this step for receipts older than the seen-nonce retention window.
4. If `ao_anchor.settle_tx` is present, verify that `ao_anchor.settle_log_index` points to a USDC `Transfer` event in that transaction and that the event's `to` field matches the producer's known `payTo` address (derivable from `iss + /.well-known/x402`). If not, reject with reason `"settle anchor mismatch"`.
5. If `ao_chain.prev` does not equal the SHA-256 hash of the immediately preceding receipt's JCS bytes (when known to the verifier — e.g. when the verifier has previously cached that hash), reject with reason `"chain hash mismatch"`. Verifiers that have not seen the predecessor MUST NOT reject on this ground — chain validation is opportunistic, not mandatory.
6. If all checks pass, insert the lookup key into the seen-nonce cache before returning success. This MUST happen atomically with the success determination to prevent races between concurrent verifications of the same receipt.

### 9.4 Producer behavior (MUST)

Producers MUST:

1. Generate `ao_nonce` using a cryptographically-secure UUIDv7 generator that derives the timestamp prefix from a monotonic source. The leading 48 bits MUST encode the receipt's issuance time per RFC 9562 §5.7.
2. Maintain a per-`kid` counter for `ao_chain.seq` that persists across producer restarts. Counter loss (e.g. catastrophic state loss) is a key-compromise event under §8.7 and MUST trigger emergency rotation.
3. Persist the JCS-canonicalized bytes of every issued receipt long enough to compute `ao_chain.prev` for the next receipt under the same `kid`. The retention requirement is the producer's signing key's full lifetime including overlap window (180 days under default v0.2 cadence).
4. NEVER issue two receipts with the same `(kid, seq)` tuple. If a producer instance crashes mid-signing, the recovery procedure MUST advance `seq` past the highest pre-crash value before issuing further receipts.

### 9.5 When the settle anchor is required

The `ao_anchor` block is REQUIRED on any receipt issued in response to a paid `/evaluate` or `/research` call (i.e. when the receipt's existence was triggered by an on-chain x402 settle). The anchor is OPTIONAL for receipts issued in response to free-tier `/preview` calls.

Verifiers MAY enforce a stricter policy — e.g. an audit-grade consumer MAY reject any receipt that does not carry an `ao_anchor`, regardless of the producer's policy. Consumer policy enforcement is unrestricted by this spec.

### 9.6 Interaction with §5 freshness axes

Replay protection is **orthogonal** to the three freshness axes specified in Section 5. A receipt may be fresh on all three axes (signature, calibration, evidence) and still be a replay; conversely, a stale receipt that is presented for the first time is not a replay.

Verifier policy SHOULD evaluate replay protection BEFORE freshness axes — a confirmed replay is a security event and is logged differently from a stale-but-genuine receipt.

### 9.7 Worked example: producer-side counter

```
Kid f27 has issued 3 receipts so far:
  receipt 1: seq=0, nonce=01926b48-..., prev=sha256:000...
  receipt 2: seq=1, nonce=01926b49-..., prev=sha256:<hash of receipt 1 JCS>
  receipt 3: seq=2, nonce=01926b4a-..., prev=sha256:<hash of receipt 2 JCS>

Kid f27 crashes and recovers from persistent storage at seq=2.
  receipt 4: seq=3, nonce=01926c11-..., prev=sha256:<hash of receipt 3 JCS>

Kid f27 issues receipt 5 concurrently from two replicas:
  ERROR. Producer MUST serialize seq increments — replicas SHALL share a
  durable counter (e.g. Redis INCR, Postgres SEQUENCE, etcd transactional
  counter) and SHALL NOT issue independently from in-process state.
```

### 9.8 Migration from v0.1

v0.1 receipts did not carry `ao_nonce`, `ao_chain`, or `ao_anchor`. Verifiers SHOULD support a transitional mode that:

- For receipts whose `kid` is listed in `transitional_modes.canonicalization.v0_1_grandfathered_kids` (Section 8.5), skip §9.3 entirely (no replay protection enforced for legacy receipts).
- For all other receipts, enforce §9.3 strictly.

Producers SHOULD NOT reissue v0.1 receipts as v0.2 — the original signing time is gone and the chain history cannot be reconstructed. Legacy receipts remain valid under the freshness rules of v0.1 only.

---

## 10. Claim Semantics (Normative)

> **Status:** New in v0.2. Closes BLOCKER #4 from v0.1 review. Resolves the calibration / provisional / historical confusion flagged by Decixa partner review on 2026-04-29.

The `ao_confidence` field is a probability in `[0,1]` — but consumers need to reason programmatically about *what kind of confidence* this number represents. v0.1 conflated calibrated, provisional, and historical confidence into a single scalar. v0.2 separates them.

### 10.1 The three confidence states

The JWS Payload MUST include a `confidence.level` field with exactly one of the following values:

| Value | Meaning | When set |
|---|---|---|
| `"calibrated"` | The confidence score is grounded against a benchmark anchor (Section 3.2.3) that was active at the time of signing AND whose calibration `valid_until` is still in the future. | Standard production receipts. |
| `"provisional"` | The confidence score is computed but the calibration anchor is either expired, missing, or has been flagged as compromised. The score is informative but not policy-grade. | When `ao_calibration.valid_until ≤ iat`, or when the anchor benchmark itself has been retracted. |
| `"historical"` | The receipt was issued under an older anchor that has since been superseded by a calibration anchor refresh. The score reflects the calibration in effect at issuance time and remains valid for audit purposes, but the consumer is on notice that the current calibration would likely score differently. | When a newer calibration anchor has been published AFTER the receipt's `iat` but the receipt itself has not staled out under §5. |

### 10.2 Programmatic rules (MUST)

Consumers MUST evaluate `confidence.level` programmatically as follows:

```
FOR_POLICY_ENFORCEMENT(receipt) ==
  confidence.level == "calibrated" AND
  ao_confidence >= consumer_policy.threshold

FOR_AUDIT_REPLAY(receipt) ==
  confidence.level IN ["calibrated", "historical"] AND
  SIGNATURE_FRESH(receipt)

FOR_INFORMATIONAL_DISPLAY(receipt) ==
  TRUE
  (i.e. all three levels are surfaceable, but provisional and historical
   MUST be visually flagged when shown to a human)
```

In other words:

- **Policy enforcement (gate an agent action):** require `calibrated`. Reject `provisional` and `historical`.
- **Audit replay (retrospective review):** accept `calibrated` and `historical`. Reject `provisional`.
- **Informational display:** all three are acceptable, but UIs MUST visually flag non-`calibrated` levels.

Consumers MAY tighten these rules (e.g. an audit-grade reviewer may require `calibrated` only) but MUST NOT loosen them.

### 10.3 Producer behavior (MUST)

Producers MUST set `confidence.level` deterministically at receipt construction time, evaluated in this order:

1. If the active calibration anchor (referenced by `ao_calibration.anchor_dataset`) is on the producer's published `compromised_anchors[]` list (Section 10.5), set `level = "provisional"`.
2. Else, if `ao_calibration.valid_until ≤ iat`, set `level = "provisional"`.
3. Else, if a newer calibration anchor has been published with `anchor_as_of > current_anchor.anchor_as_of` AND the producer is in a transition window during which both anchors are active, set `level = "calibrated"` (the producer's choice of anchor for THIS receipt determines the level — newer-anchor receipts are also `calibrated`, just under a different anchor).
4. Else, set `level = "calibrated"`.

Note: `"historical"` is NEVER set by the producer at issuance time. It is set by the **verifier** retrospectively when it observes that a newer anchor has been published after the receipt's `iat`. The verifier rewrite is in-memory only — it MUST NOT modify the original signed payload.

### 10.4 Verifier behavior (MUST)

Verifiers MUST evaluate `confidence.level` as follows:

1. Read `confidence.level` from the receipt payload.
2. If `confidence.level == "calibrated"`, check whether the receipt's referenced calibration anchor (`ao_calibration.anchor_dataset` + `anchor_as_of`) is still the active anchor for `iss`. The active anchor is determined by querying `iss + /.well-known/agentoracle/calibration-anchor.json` (see Section 10.5).
3. If the receipt's anchor matches the current active anchor, the level remains `"calibrated"`.
4. If the receipt's anchor is NOT the current active anchor but is listed in the issuer's `calibration_anchor.history[]`, the verifier MUST surface this receipt as effective level `"historical"`. The on-the-wire bytes remain `"calibrated"` — only the verifier's report SHALL rewrite.
5. If the receipt's anchor is in the issuer's `calibration_anchor.compromised[]`, surface as `"provisional"` regardless of what the bytes say.

Verifiers MUST NOT modify the on-the-wire receipt bytes when surfacing a historical or provisional re-classification. The rewrite is presentational only.

### 10.5 Calibration anchor metadata endpoint

Issuers MUST publish a calibration anchor metadata document at:

```
https://<iss>/.well-known/agentoracle/calibration-anchor.json
```

With the following structure:

```json
{
  "active": {
    "anchor_dataset": "AVeriTeC-2024-dev-500",
    "anchor_seed": 42,
    "anchor_as_of": "2026-05-13",
    "valid_until": "2026-11-13T00:00:00Z"
  },
  "history": [
    {
      "anchor_dataset": "FEVER-1.0-paper_dev-200",
      "anchor_seed": 42,
      "anchor_as_of": "2026-04-21",
      "superseded_at": "2026-05-13T00:00:00Z",
      "superseded_by": "AVeriTeC-2024-dev-500"
    }
  ],
  "compromised": []
}
```

The document MUST be served with `Cache-Control: max-age=3600` or shorter. Verifiers SHOULD refresh their cached copy at least every 6 hours.

### 10.6 Worked example: confidence level transitions

```
2026-04-21: Producer publishes anchor FEVER-1.0-paper_dev-200.
  Receipt R1 issued with anchor_dataset=FEVER-1.0-...; level=calibrated.

2026-05-13: Producer publishes new anchor AVeriTeC-2024-dev-500.
  history[] now contains FEVER-1.0; active is AVeriTeC.
  Receipt R1's on-the-wire bytes still say level=calibrated.
  When a verifier sees R1 today, it reports R1's effective level as
    "historical" because R1's anchor is in history[] not active.
  R1 remains valid for audit replay but cannot gate new agent actions.

2026-05-20: Producer flags FEVER-1.0 as compromised (e.g. evaluation set
  contamination discovered).
  compromised[] now contains FEVER-1.0.
  When a verifier sees R1 now, it reports R1's effective level as
    "provisional". R1 is no longer valid for audit replay either.
```

### 10.7 Open question: monotonic anchor versioning

The semantics above assume calibration anchors form a single linear history per issuer. A future revision MAY accommodate parallel anchors (e.g. FEVER for general-domain claims AND a domain-specific medical anchor running concurrently). v0.2 leaves this in Section 11 (Open Questions).

### 10.8 Migration from v0.1

v0.1 receipts did not include `confidence.level`. Verifiers SHOULD treat all v0.1 receipts as effective level `"historical"` once v0.2 ships in production, since the absence of explicit calibration evidence in v0.1 makes them ineligible for policy enforcement under v0.2 rules.

---

## 11. Open Questions

The following items are intentionally underspecified pending discussion:

1. **COSE encoding** — should the spec include a normative COSE binding alongside JWS for embedded-device consumers?
2. **Multi-issuer receipts** — when verification spans multiple oracles (e.g. AgentOracle + a different content authenticity verifier), should the receipt support multi-signature attestation, or should consumers verify N separate single-signer receipts?
3. **Calibration anchor versioning** — when the underlying benchmark dataset itself revises (FEVER 1.0 → 2.0), how do we name and reference both versions without breaking existing consumers? Section 10.7 surfaces a related case: parallel anchors for different domains.
4. **Evidence URI authentication** — proposed: caller's bearer presentation matches `sub`. Alternative: signed evidence URI that delegates access for a TTL.
5. **Privacy** — when `ao_claim.redacted == true`, the `text` field is omitted and only `hash` is present. Does this provide adequate privacy guarantees for content-team consumers verifying brand-sensitive claims pre-publication?
6. **Replay protection across issuers** — Section 9 scopes the seen-nonce cache to `(iss, kid, ao_nonce)`. If two different issuers happen to mint colliding nonces (theoretically impossible under UUIDv7 randomness, but worth noting), the cache correctly treats them as distinct. Should the spec mandate a stronger global-uniqueness rule, or is per-issuer scoping sufficient?
7. **Settle anchor for non-EVM chains** — Section 9.2's `ao_anchor.settle_chain` uses CAIP-2; Solana and Stellar settles are within scope. The corresponding `settle_log_index` semantics need clarifying for non-EVM chains.

---

## 12. Status, Contribution, and Discussion

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
