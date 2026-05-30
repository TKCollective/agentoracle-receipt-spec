# ADR-002: Canonical Recommendation, Derived Gate, Versioned Mapping Binding

**Status:** Proposed (v0.3 draft, refines ADR-001)
**Date:** 2026-05-30
**Originator:** External review by [@beenz](https://github.com/headlessoracle) (Headless Oracle, IETF `draft-msebenzi-environment-state-00` author), follow-up review of ADR-001.
**Refines (does not supersede):** [ADR-001](./ADR-001-binary-halt-gate.md). Binary-halt gate semantics remain. This ADR specifies *how the gate appears in the signed receipt* so a verifier can recompute it from signed inputs.

## Context

ADR-001 collapsed the multi-band recommendation to a binary `act` / `halt` gate. While drafting the receipt schema for v0.3, two candidate signing strategies surfaced:

**Option 1: Sign both recommendation and gate as co-equal fields.**
- Re-introduces the "two-fields-can-disagree" seam class — the exact bug fixed in [agentoracle-eval-harness@f6a75e3](https://github.com/TKCollective/agentoracle-eval-harness/commit/f6a75e3) — one layer up. Rejected.

**Option 2: Sign only the gate; put recommendation in unsigned header as evidence.**
- The gate is a pure function of the recommendation under a fixed mapping. Signing the output but not the input means a downstream verifier cannot recompute the gate from signed data. They have to trust our runtime executed the mapping correctly. For a "don't trust, verify" product, this is the *one* field that must not be uncheckable. Rejected.

External review framed the gap precisely:

> *Under the collapse we just agreed, the gate outcome isn't independent of the recommendation. It's a pure function of it — ACT exactly when recommendation is a confident affirmative, HALT otherwise. So if you sign only the gate and push recommendation into the header as evidence, you've signed the output of the mapping but not the input. A downstream verifier then can't recompute the gate from signed data — they have to trust your mapping ran correctly. That's the one step that actually makes the decision, and it's the step you'd be asking them to take on faith.*

And the version-binding concern:

> *Your collapse rules will change — you'll tighten what counts as a confident affirmative, fold some new verdict value into HALT. A receipt signed under v1 has to stay verifiable as correct-under-v1 after v2 ships. No version field and a future rules change either silently invalidates old receipts or re-verifies them to a different gate. Same class of bug as the harness seam, receipt layer.*

## Decision

**Sign the recommendation as the canonical claim. Sign the gate as a derived field. Bind them with a published, versioned mapping identifier. The JWS signature covers all three together.**

### Receipt structure (v0.3)

```json
{
  "v_verdict": "supported",                          // raw truth label
  "v_recommendation": "confident_supported",         // canonical input (signed)
  "v_gate": "act",                                   // derived output (signed)
  "v_gate_mapping": "v0.3.0-2026-05-30",             // ruleset identifier (signed)
  "v_confidence": 0.87,                              // provenance (signed, not gating)
  "v_gate_threshold": 0.70,                          // provenance (signed, not gating)
  "v_adversarial_result": "resilient",               // provenance (signed, not gating)
  "v_sources_used": ["sonar", "adversarial"],        // provenance (signed, not gating)
  ...
}
```

### `v_recommendation` enum (canonical input)

| Value | Definition |
|---|---|
| `confident_supported` | `v_verdict == supported` AND `v_confidence ≥ v_gate_threshold` AND `v_adversarial_result ∈ {resilient, not_checked}` |
| `vulnerable_supported` | `v_verdict == supported` AND `v_adversarial_result == vulnerable` |
| `weak_supported` | `v_verdict == supported` AND `v_confidence < v_gate_threshold` |
| `refuted` | `v_verdict == refuted` |
| `unverifiable` | `v_verdict == unverifiable` |
| `error` | Runtime error / timeout / no sources retrieved |

The recommendation is itself derived from `v_verdict`, `v_confidence`, `v_gate_threshold`, `v_adversarial_result` — all of which are also signed. A verifier can fully recompute the recommendation from signed primitives, then recompute the gate from the recommendation under the named mapping.

### `v_gate_mapping` semantics

`v_gate_mapping` is a stable string identifier of a published mapping document, e.g. `v0.3.0-2026-05-30`. The mapping document is hosted at a permanent URL and registered in this repository under `mappings/<id>.md`. Each published mapping is immutable after publication. Future mapping revisions ship as new IDs (`v0.4.0-...`, `v0.3.1-...`), never as rewrites.

For `v_gate_mapping = "v0.3.0-2026-05-30"`:

```
gate(rec) = act   if rec == "confident_supported"
gate(rec) = halt  otherwise
```

### Verification protocol

A receipt verifier executes:

```
1. Verify JWS signature over the receipt JSON (RFC 7515).
2. Resolve v_gate_mapping → fetch the named mapping document (cache by ID).
3. Recompute candidate_recommendation from
   (v_verdict, v_confidence, v_gate_threshold, v_adversarial_result)
   using the rules in §"v_recommendation enum" above.
4. Confirm candidate_recommendation == v_recommendation.
5. Recompute candidate_gate = mapping(v_recommendation).
6. Confirm candidate_gate == v_gate.
7. If all match → receipt is valid AND internally consistent under mapping.
   Any mismatch → receipt is malformed; treat as halt.
```

A verifier never trusts the issuer's runtime to have applied the mapping. The signature binds the inputs, the outputs, and the mapping identifier together; the verifier recomputes locally.

## Rationale

1. **No trust in the runtime.** The verifier recomputes the gate from signed inputs. The signature binding is end-to-end.
2. **No two-fields-can-disagree seam.** Both fields are signed, but the mapping identifier makes them provably consistent. Inconsistency is a malformed-receipt condition, not an "interpretation" question.
3. **Forward-compatible.** When the mapping evolves (`v0.4.0-...`), v0.3.0-signed receipts remain *correct under v0.3.0* forever. A verifier reading a v0.3.0 receipt fetches the v0.3.0 mapping doc and validates against it. No silent semantic drift.
4. **Mapping changes are public, immutable, and auditable.** The mapping document at `mappings/v0.3.0-2026-05-30.md` is git-tracked and can be referenced by IETF I-D, tutorials, partner integrations. When v0.4.0 ships, it ships as a new file with its own ADR.
5. **Recommendation is not provenance.** External review:
   > *Your instinct that "the gate is the contract, everything else is provenance" is right about the confidence numbers and wrong about the recommendation: the recommendation isn't provenance, it's the input the contract is computed from. Don't demote it.*

## Consequences

### Breaking changes (vs ADR-001 draft state)

- `v_recommendation` enum changes from `{act, halt}` to `{confident_supported, vulnerable_supported, weak_supported, refuted, unverifiable, error}`. The gate moves to a new field `v_gate ∈ {act, halt}`.
- New required signed field `v_gate_mapping`.
- README schema table updated below.

### Non-breaking (vs ADR-001 conclusions)

- Binary gate semantics: unchanged (still `act` / `halt`, still fail-closed).
- Differentiator: unchanged (still pre-action fail-closed gate vs SCITT/RATS/W3C VC CM).
- Sibling-family argument: strengthened (`environment.market_state == OPEN → act` and `verification.v_gate == act` now share both shape and the explicit "recompute from signed inputs" verification protocol).

### Repository additions

- `mappings/v0.3.0-2026-05-30.md` — first published mapping document. Created in this branch.
- README `§ Receipt verification protocol` section added.
- IETF I-D outline updated with the canonical/derived/version-binding model.

## Open Questions

1. **OQ-1: `confident_supported` strictness.** Should `not_checked` adversarial be treated the same as `resilient`? Current decision: yes, for v0.3.0 — adversarial coverage is opt-in. Revisit when adversarial probing becomes default. (Logged here; not blocking.)
2. **OQ-2: Mapping document hosting.** Repo-only (git source-of-truth) or also IANA-registered registry? Current decision: repo-only for v00; IANA registration deferred to v01 of the I-D after WG feedback.
3. **OQ-3: Backward compatibility shim.** When `?spec=v0.2` is requested, what does `v_recommendation` carry? Current decision: the v0.2 four-band value (`act|verify|reject|abstain`). The shim emits a v0.2 schema, not a v0.3 schema with a v0.2-shaped recommendation field. Documented in the shim's own ADR when implemented.

## References

- External review thread continuation: Coinbase Developer Discord #x402 + DMs, May 29–30, 2026.
- [ADR-001](./ADR-001-binary-halt-gate.md): binary-halt collapse (this ADR refines, does not supersede).
- IETF I-D outline (workspace): updated section 4.2 and 5.x to reflect canonical/derived/version model.
- Reproducibility seam precedent: [agentoracle-eval-harness@f6a75e3](https://github.com/TKCollective/agentoracle-eval-harness/commit/f6a75e3) — same class of bug, harness layer.
