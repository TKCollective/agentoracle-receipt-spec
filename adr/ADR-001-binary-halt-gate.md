# ADR-001: Binary-Halt Gate Semantics

**Status:** Proposed (v0.3 draft)
**Date:** 2026-05-29
**Originator:** External review by [@beenz](https://github.com/headlessoracle) (Headless Oracle, IETF `draft-msebenzi-environment-state-00` author), Coinbase Developer Discord #x402 thread + follow-up review of receipt spec v0.2.
**Supersedes:** Multi-band `recommendation` field in receipt spec v0.1 / v0.2 (`act` | `verify` | `reject` | `abstain`).

## Context

Receipt spec v0.1 and v0.2 exposed two parallel signals at the gate consumed by agent code:

1. **`ao_verdict`** ∈ {`supported`, `refuted`, `unverifiable`} — the underlying truth label.
2. **`recommendation`** ∈ {`act`, `verify`, `reject`, `abstain`} + a `[0,1]` confidence — a four-band action signal layered on top.

Agents consuming `/evaluate` had to interpret which band meant "safe to proceed." This created two architectural problems:

### Problem 1: Family-fit with environment.*

The pitch for the proposed `verification.*` constraint family (ADR scope: sibling-to-environment, not sub-member) is that pre-action verification fails-closed the same way `environment.market_state == OPEN` fails-closed in Mastercard Verifiable Intent. But `environment.*` is binary (state matches or it doesn't, halt or proceed), while v0.1 / v0.2 `recommendation` was four-band. The sibling-family argument was weakened by the gate shapes not matching.

External review framed this as:

> *Sibling, not member, for verification.\* family. Gate shape must match.*

### Problem 2: Crowded pool — what is the differentiator?

The pre-action verification space now has multiple credible standards proposals:

| Project | Layer | Shape |
|---|---|---|
| SCITT (RATS WG) | Signing / receipt | Receipt envelope only — no gate semantics |
| RATS Evidence→Verifier→AR→RP | Attestation flow | Multi-step trust chain |
| VAP framework (`draft-kamimura-vap-framework`) | Verifier abstraction | Framework, not a gate |
| W3C VC Confidence Method (Oct 2025 WD) | Verifiable Credentials | Confidence as sidecar, no halt primitive |

AgentOracle's differentiator is **the pre-action fail-closed gate**, not the signing machinery (SCITT already does that) and not confidence quantification (W3C already does that). A four-band gate undermines the differentiator because consumers have to write their own halt logic against a confidence threshold — i.e. AgentOracle becomes a confidence provider, not a gate.

External review:

> *Differentiate on pre-action fail-closed gate, not signing machinery. Receipt carries nuance; gate stays binary.*

## Decision

**Collapse the multi-band `recommendation` field to a binary gate signal:**

```
recommendation ∈ { "act", "halt" }
```

Mapping from underlying signals:

| `ao_verdict` | `ao_confidence` | adversarial_result | `recommendation` |
|---|---|---|---|
| `supported` | ≥ threshold | `resilient` or `not_checked` | `act` |
| `supported` | ≥ threshold | `vulnerable` | `halt` |
| `supported` | < threshold | (any) | `halt` |
| `refuted` | (any) | (any) | `halt` |
| `unverifiable` | (any) | (any) | `halt` |
| (any) — runtime error / timeout / no sources | (any) | (any) | `halt` |

Default threshold is `0.70` (matches current v0.2 `verify`/`act` split). Consumers MAY require higher thresholds via mandate policy (see §6); they MAY NOT lower the threshold — the gate is the floor.

**Confidence and verdict_raw remain in the receipt as metadata.** They are signed, auditable, and available for downstream reasoning (UI surfacing, retry policy, calibration drift detection). They are NOT consumed by the gate.

## Rationale

1. **Sibling-family criterion is satisfied.** `verification.factual_claim_state ∈ {act, halt}` is shaped identically to `environment.market_state ∈ {open, closed}`. Both are pre-action fail-closed primitives. The proposed sibling structure now defends cleanly.
2. **Differentiator is sharpened.** SCITT signs receipts but has no gate. W3C VC Confidence Method exposes confidence but has no halt. AgentOracle is the only proposal in the pool that ships a verified, fail-closed action gate. The four-band recommendation diluted that claim.
3. **Receipt nuance is preserved.** Calibration, confidence, verdict_raw, evidence pointers, adversarial flags all remain in the signed JWS. Auditors and policy engines get the full picture; agents at the call-site get a single decision.
4. **Reduces consumer integration surface.** A LangChain / CrewAI / MCP integration becomes one branch (`if rec == "act": proceed else: halt`). Today it's a four-way switch consumers tend to collapse incorrectly.
5. **Calibration discipline.** Threshold is a single number with provenance (`ao_calibration.anchor_dataset` + `anchor_seed`), not four tunable bands each demanding its own justification.

## Consequences

### Breaking changes

- `/evaluate` response `recommendation` field: `act|verify|reject|abstain` → `act|halt` (v2.3).
- Receipt schema: `recommendation` enum narrows. Field rename to `recommendation_v3` is rejected — keeping the field name preserves migration legibility.
- Tutorial #4 example output and all SDK code samples need updating.
- Receipt spec v0.2 examples in `examples/` re-issued under v0.3.

### Non-breaking changes

- `ao_verdict`, `ao_confidence`, `ao_calibration`, `ao_sources_used`, adversarial fields unchanged.
- JWS envelope, JWKS, key rotation, multi-axis freshness all unchanged.
- AVeriTeC scoring methodology unchanged — accuracy numbers (57.6% full / 57.7% held-out) are computed from `verdict_raw`, not from `recommendation`, so binary-halt has no effect on benchmark score. See [agentoracle-eval-harness](https://github.com/TKCollective/agentoracle-eval-harness) `scripts/score.py`.

### Public positioning

- Marketing language: "Pre-action verification gate" — no qualifier on "confidence layer."
- Landing page: replace "confidence scoring" copy with "act / halt verification gate."
- README hero one-liner: "Verify before you act. Binary gate. Signed receipts."

### Risks

- **Risk:** Existing integrators using `verify` band see breaking change.
  **Mitigation:** Maintain v2.2 `/evaluate` for one minor cycle behind a `?spec=v0.2` query flag. Deprecation notice in changelog; remove at v2.4 / receipt v0.4.
- **Risk:** Consumers wanting "soft halt" (warn but proceed) lose that affordance.
  **Mitigation:** They can read `ao_confidence` from the receipt and implement their own soft-halt layer. The gate stays fail-closed; soft policies are a consumer concern.
- **Risk:** Threshold of 0.70 is calibrated to current model + retrieval stack. Drift breaks the gate.
  **Mitigation:** `ao_calibration.valid_until` already gates this. When calibration ages out, receipts are stale and consumers SHOULD re-evaluate.

## Open Questions

1. **OQ-1: Naming.** `act` / `halt` vs `proceed` / `halt` vs `go` / `stop`. Resolution: stay with `act` / `halt` for symmetry with `ao_verdict` already namespaced under `ao_*`, and because `halt` is the verb shared with `environment.*` family. Decision logged here; revisit if W3C VC CM adopts different terminology.
2. **OQ-2: Soft-halt opt-in.** Should there be an optional `recommendation_soft` field that exposes the original four-band signal for consumers who explicitly opt into nuance? Inclination: no. Adding it back undermines the differentiator argument. If a serious integrator needs it, they read `confidence` and decide.
3. **OQ-3: Threshold parameterization.** Should the threshold be exposed in receipt metadata so consumers can verify which threshold gated the response? **Yes.** Adding `ao_gate_threshold: 0.70` as a required receipt field in v0.3.

## References

- External review thread: Coinbase Developer Discord #x402, follow-up DMs May 28–29, 2026.
- Sibling-family discussion: [Beenz / headlessoracle](https://github.com/headlessoracle) `draft-msebenzi-environment-state-00`.
- Pool comparison: [SCITT](https://datatracker.ietf.org/wg/scitt/), [RATS](https://datatracker.ietf.org/wg/rats/), [draft-kamimura-vap-framework](https://datatracker.ietf.org/doc/draft-kamimura-vap-framework/), [W3C VC Confidence Method](https://www.w3.org/TR/vc-confidence-method/).
- AgentOracle eval harness reproducibility seam fix: [TKCollective/agentoracle-eval-harness@f6a75e3](https://github.com/TKCollective/agentoracle-eval-harness/commit/f6a75e3).

## Implementation Plan

| Item | Owner | Target |
|---|---|---|
| ADR-001 (this doc) | TKCollective | 2026-05-29 ✓ |
| Receipt spec v0.3 README update | TKCollective | 2026-05-30 |
| `/evaluate` v2.3 server change behind feature flag | TKCollective | 2026-06-02 |
| `?spec=v0.2` back-compat shim | TKCollective | 2026-06-02 |
| Tutorial #4 example refresh | TKCollective | 2026-06-04 |
| Landing page copy update | TKCollective | 2026-06-04 |
| SDK example refresh (LangChain, CrewAI, MCP) | TKCollective | 2026-06-05 |
| Receipt spec v0.3 cut + ship | TKCollective | 2026-06-05 |
| Co-author hold | — | Until external builders demonstrate independent adoption (see external review) |
