# Changelog

## v0.2 (in progress) — May 2026

> **Status:** Work in progress. Targeted finalization: May 14-16, 2026.
> Targeted IETF Internet-Draft filing: June 5-10, 2026.

Closes the 7 BLOCKER gaps identified in the v0.1 review.

### Added (Normative)

- **Section 7 — Canonicalization.** All signatures MUST be computed over the RFC 8785 JCS-canonical byte representation of the JWS payload. Includes verifier re-canonicalization rule (independent of signature validation), worked example, reference-implementation pointers per language, and a v0.1 → v0.2 grandfathering policy. *Closes BLOCKER #1.*
- **Section 8 — Key Rotation Policy.** Mandatory 90-day rotation cadence with 90-day overlap window. Specifies `kid` format (`ao-receipt-{YYYY}-{MM}-{algorithm}-{8-hex}`), JWKS metadata extensions (`activated_at`, `deactivated_at`, `expires_at`), a 7-step `kid` resolution algorithm verifiers MUST follow exactly, emergency rotation procedure, and a `transitional_modes` JWKS block for cutover bookkeeping. *Closes BLOCKER #2.*
- **Section 9 — Replay Protection.** Adds `ao_nonce` (UUIDv7), `ao_chain` (per-`kid` hash chain with `prev` + `seq`), and optional `ao_anchor` (settle-tx + CAIP-2 chain + log index) as MUST fields. Verifiers maintain a seen-nonce cache keyed on `(iss, kid, ao_nonce)` with 7-day default retention. Settle-anchored receipts MAY be additionally validated against on-chain finality. Producer recovery rules cover replica races and crash recovery. v0.1 grandfathering pulls the canonicalization cutover policy in by reference. *Closes BLOCKER #3.*
- **Section 10 — Claim Semantics.** Resolves the calibration / provisional / historical confusion flagged by Decixa partner review on 2026-04-29. Adds `confidence.level: calibrated | provisional | historical` with strict programmatic semantics: `calibrated` only for policy enforcement, `calibrated` + `historical` for audit replay, all three surfaceable for informational display. Producers set the level deterministically at signing time; verifiers MAY surface a retrospective re-classification when newer / compromised anchors land, but MUST NOT modify the on-the-wire receipt bytes. Mandates a new metadata document at `/.well-known/agentoracle/calibration-anchor.json` for active / history / compromised anchor lookup. *Closes BLOCKER #4 and the calibration-provisional ambiguity from BLOCKER #5.*

### Renumbered

- Section 7 (was "Open Questions") → **Section 11**
- Section 8 (was "Status, Contribution, and Discussion") → **Section 12**

### Still to land in v0.2

- `kid` resolution edge cases beyond §8.6 (full lookup-failure decision tree) — BLOCKER #6
- Receipt format versioning: how v0.2 → v1.0 migration is signaled and grandfathered — BLOCKER #7

These two remaining blockers are scheduled for May 14–16 (in parallel with the AVeriTeC harness ship + Beenz intro).

### Why this slip is intentional

The IETF Internet-Draft filing date moves from May 28 to June 5–10. This is an accepted slip, not a failure. Rationale: the canonicalization and key rotation sections in v0.2 are normative and will be referenced by every downstream verifier implementation forever. Rushing them produces irreversible interop bugs across the consumer base. A 7-day slip prevents that.

External communications (BDB application, angel pitch, etc.) characterize the spec as: "Receipt spec v0.2 shipping this week, IETF Internet-Draft filing in early June. Wanted to get canonicalization and key rotation right rather than rush."

---

## v0.1 — Apr 29, 2026

Initial public draft. JWS-signed receipt format with multi-axis (signature / calibration / evidence) freshness verification, W3C VC Confidence Method alignment, and composability hooks for Decixa `trust_evidence` and Mastercard Verifiable Intent.

Published in response to the Coinbase Developer Discord #x402 thread, Apr 29, 2026.

Known gaps documented in v0.1 review (now scheduled for v0.2): canonicalization, key rotation, replay protection, claim semantics partitioning, calibration.provisional rules, kid resolution edge cases, format versioning.
