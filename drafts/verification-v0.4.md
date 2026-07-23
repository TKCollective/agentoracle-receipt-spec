# verification.v0.4 — Draft Extension: Sealed Evidence & Multi-Clock Anchoring

**Status:** DRAFT FOR DISCUSSION — not yet normative. Comments welcome via issues/PRs.
**Extends:** verification.v0.3 (and v0.3+composed). Fully backward-compatible: every valid v0.3 envelope remains valid; v0.4 fields are additive.
**Author:** Joe Krausz, AgentOracle (TK Collective LLC)
**Date:** 2026-07-24

---

## 1. Motivation

verification.v0.3 makes the *record* tamper-evident: canonical bytes (RFC 8785), Ed25519 JWS (RFC 7515/8037), published JWKS (RFC 7517), offline verification. Two gaps remain between a v0.3 receipt and the strongest evidence artifact the same primitives can support:

1. **Evidence drift.** A receipt binds a *reference* to the evidence consulted, but the referenced content can change or disappear after signing. "We checked source X" weakens over time because X is mutable. An examiner years later cannot confirm what X said at verification time.

2. **Single-clock precedence.** Optional on-chain anchoring (v0.3 §anchoring) proves a record existed before a block timestamp — one clock, one trust domain. Different examiners trust different clocks: a DeFi counterparty trusts an EVM chain; a court or regulator trusts an RFC 3161 timestamping authority; a neutrality-maximalist trusts Bitcoin. One clock forces the examiner into one trust domain.

v0.4 closes both gaps with two additive field groups: **sealed evidence** and **multi-clock anchors**.

## 2. Sealed Evidence

### 2.1 The `evidence_seals` array

A v0.4 payload MAY include `evidence_seals`, an array of seal objects, one per evidence item consulted. Each seal object contains:

| Field | Req | Description |
|---|---|---|
| `ref` | MUST | The evidence reference exactly as it appears in the v0.3 `evidence` set (URI or identifier). Every entry in `evidence_seals` MUST correspond to an entry in `evidence`. |
| `content_sha256` | MUST | Lowercase hex SHA-256 of the retrieved evidence bytes (see 2.2 for what is hashed). |
| `retrieved_at` | MUST | RFC 3339 UTC timestamp of retrieval. |
| `media_type` | MUST | MIME type of the hashed representation (e.g. `text/html`, `application/pdf`, `application/json`). |
| `content_length` | SHOULD | Byte length of the hashed representation. |
| `snapshot_ref` | MAY | Content-addressed locator of an archived copy (e.g. a WACZ archive path, IPFS CID, or HTTPS URL to an archive). The locator's content, when retrieved, MUST hash to `content_sha256` (for raw snapshots) or contain a member that does (for container formats; the member path MUST be included, e.g. `wacz:archive.wacz!data/pages/p1.html`). |
| `fetch_attestation` | MAY | Reserved for a future extension: a third-party proof that the content was served by the origin (e.g. a TLS-transcript proof). Structure intentionally unspecified in v0.4; verifiers MUST ignore unrecognized members. |

### 2.2 What is hashed

`content_sha256` is computed over the **decoded response body bytes** as received (after transfer-decoding, before any rendering, extraction, or normalization). For dynamic pages, the seal attests to *the bytes the verifier's fetch received at `retrieved_at`* — no more, no less. Implementations SHOULD record `media_type` faithfully so examiners understand what representation was sealed.

### 2.3 Verification semantics

Because `evidence_seals` sits inside the signed canonical payload, seals are covered by every signature in the envelope. Verifiers:

- MUST fail an envelope where an `evidence_seals` entry references a `ref` absent from `evidence` (`evidence_seal_unmatched`).
- MUST, when a `snapshot_ref` is resolvable, verify that the snapshot content hashes to `content_sha256`; a mismatch is `evidence_snapshot_mismatch`.
- MUST NOT fail an envelope solely because a `snapshot_ref` is unresolvable (archives may be offline); the appropriate result is a warning (`evidence_snapshot_unavailable`) with the envelope otherwise PASS-eligible.
- MUST treat absence of `evidence_seals` as valid v0.3 behavior (backward compatibility).

### 2.4 What sealing does and does not prove

A seal proves the issuer committed, at signing time, to specific evidence bytes with a specific hash. With a resolvable snapshot, an examiner can read exactly what the verifier read. Sealing does **not** by itself prove the bytes genuinely originated from the referenced origin (that is the province of `fetch_attestation`, future work), and does not make the evidence true. This section's honesty discipline mirrors v0.3: state precisely what is proven, and no more.

## 3. Multi-Clock Anchors

### 3.1 The `anchors` array

A v0.4 envelope MAY carry `anchors`, an array of anchor objects **outside** the signed payload (anchoring necessarily happens after signing). Each anchor binds the envelope's canonical hash — or a Merkle root committing to it — to an external clock. Anchor object fields:

| Field | Req | Description |
|---|---|---|
| `type` | MUST | One of: `evm-tx`, `ots` (OpenTimestamps), `rfc3161`, or a collision-resistant custom string. |
| `target_sha256` | MUST | The canonical envelope hash this anchor commits to. |
| `merkle_proof` | MAY | If the anchor commits to a batch root rather than the single hash: an inclusion proof (array of lowercase hex sibling hashes, leaf-to-root order) plus `merkle_root`. Verifiers MUST recompute the root from `target_sha256` + proof. |
| `anchor_data` | MUST | Type-specific locator/proof: for `evm-tx`, chain ID + tx hash; for `ots`, the base64 OTS proof file; for `rfc3161`, the base64 DER TimeStampToken. |
| `anchored_at` | SHOULD | The external clock's reading (block timestamp / attested time), RFC 3339 UTC. |

### 3.2 Verification semantics

- Each anchor verifies **independently**; anchors are additive evidence, not a quorum. An envelope with three anchors where one is unverifiable and two verify yields two verified precedence proofs and one warning — not a failure.
- For `evm-tx`: the referenced transaction's data MUST contain `target_sha256` or the recomputed `merkle_root`.
- For `ots`: the OTS proof MUST verify against the Bitcoin chain per the OpenTimestamps protocol.
- For `rfc3161`: the TimeStampToken MUST verify per RFC 3161 against the TSA's certificate chain, over `target_sha256` (or `merkle_root`).
- Precedence claims take the form: *this envelope's hash existed at or before clock C's reading T* — per clock, never aggregated into a single "true time."

### 3.3 Rationale: clock diversity over clock count

Three anchor types span three trust domains (an EVM chain's consensus, Bitcoin's proof-of-work via OTS, and X.509 TSA infrastructure). An examiner verifies precedence against whichever clock their institution already trusts. Implementations SHOULD prefer batching (Merkle roots over receipt sets) for cost and scale; inclusion proofs keep per-receipt verifiability intact.

## 4. Conformance (planned vector classes)

Accept: seal set matching evidence, resolvable snapshot round-trip, single-anchor each type, batched anchor with valid inclusion proof. Reject: `evidence_seal_unmatched`, `evidence_snapshot_mismatch`, inclusion proof recomputing to wrong root, `rfc3161` token over wrong hash. Warning-class: `evidence_snapshot_unavailable`, single unverifiable anchor among verified ones. Vector files to follow in `examples/v0.4/` before this draft is marked normative.

## 5. Compatibility & rollout

v0.3 verifiers ignore unknown fields and continue to PASS valid envelopes (unchanged core semantics). v0.4-aware verifiers add the checks above. `typ` remains versioned; envelopes using v0.4 fields SHOULD declare `application/vnd.verification.v0.4+jws` (or `+composed+jws`) so verifiers can select the check set. Reference implementations (Node + Python, byte-identical output) will accompany the normative revision, per the project's standing conformance discipline.

---

*Comments, hostile readings, and independent implementations welcome — that's the point of publishing this as a draft.*
