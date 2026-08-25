# `verification.v0.4+composed` - conformance fixtures (Phase 3)

Composed envelope, up to four co-signers over one canonical payload (JWS general
serialization). AgentOracle (`v_gate`), AgentTrust (`v_gate_skill`) and Presidio
(`screen_ref`) carry over from the v0.3-composed suite unchanged; **Phase 3 adds
Argentum (`delegation_chain_ref`)** as an additive fourth sibling pointer plus
signature. The v0.3-composed suite is untouched: it keeps its own directory and
every one of its fixtures, keys and manifest entries is unchanged byte-for-byte.

`delegation_chain_ref` is a `delegation-chain-ref-v1` content address over a
multi-hop authority chain. Its block carries the chain artifact and the leaf
preimage, so verifiers recompute both the chain ref and the leaf `action_ref`
rather than trusting either. It answers authority provenance, never action
identity, and per `delegation-chain-ref.md` invariant 4 it is envelope-only: it
never enters an `action_ref` preimage.

Spec references:
- `../../README.md` - Mycelium Trails section, sibling-pointer model
- IETF `draft-krausz-verification-state-01` - envelope grammar, AND_PRESENT rule
- giskard09/argentum-core - `delegation-chain-ref-v1` at `16e140a`, `action-ref-v1`
  at `16dbc92`, `signing-trust-ref-v1`, `mycelium-provider-protocol`

## What's in here

```
build_fixtures.py        - regenerate everything from scratch (writes keys,
                           payloads, signatures, vectors.json)
verify.mjs               - Node.js stdlib verifier (node:crypto + vendored JCS)
verify.py                - Python stdlib + cryptography sibling verifier
vectors.json             - suite manifest (accept + reject vectors, expected
                           canonical SHA-256, signer kids, composition flags)
payload-008.json         - accept-vector payload (pre-JCS object form)
jws-008.json             - accept-vector JWS general serialization (four-signer)
payload-r{05,06}.json    - reject-vector payloads
jws-r{05,06}.json        - reject-vector JWS general serializations
jwks-agentoracle.json    - Ed25519 public key (kid ao-fixture-v0.4-composed-2026-08)
jwks-agenttrust.json     - Ed25519 public key (kid at-fixture-v0.4-composed-2026-08)
jwks-presidio.json       - Ed25519 public key (kid presidio-fixture-v0.4-composed-2026-08)
jwks-argentum.json       - Ed25519 public key (kid argentum-fixture-v0.4-composed-2026-08)
```

Vector ids continue the v0.3-composed sequence rather than restarting, so an id
stays unique across both suites when it is cited on its own.

## Coverage

### Accept vectors (must verify end-to-end)

| ID       | Scenario                                                                                | composed_decision | Chain |
|----------|-----------------------------------------------------------------------------------------|-------------------|-------|
| comp-008 | Four-signer: AO + AT + Presidio + Argentum. Two-hop chain narrows `x402:*` to `x402:payment`. | `act`       | valid |

### Reject vectors (must fail for the stated reason)

| ID       | Failure mode                                                        | `expected_failure`                    |
|----------|---------------------------------------------------------------------|---------------------------------------|
| comp-r05 | Hop 1 widens scope: `x402:payment` to `x402:*`                       | `delegation_chain_ref_scope_widening`  |
| comp-r06 | Chain continuity broken: `hops[0].delegatee != hops[1].delegator`    | `delegation_chain_ref_chain_break`     |

Both reject vectors keep root anchoring, the chain content address, and
`leaf_action_ref` binding valid, so each reject isolates exactly one invariant.

## The `delegation_chain_ref` sibling

```json
"delegation_chain_ref": {
  "issuer": "argentum",
  "verdict": "act",
  "chain": {
    "chain_id": "...",
    "hops": [ { "delegatee": "...", "delegator": "...", "delegation_ref": "...", "scope": "..." } ],
    "leaf_action_ref": "...",
    "root_delegator": "...",
    "scope": "...",
    "version": "delegation-chain-ref-v1"
  },
  "leaf_preimage": { "agent_id": "...", "action_type": "...", "scope": "...", "timestamp": "..." },
  "delegation_chain_ref": "...",
  "mapping_id": "argentum-delegation-chain-v0.1-2026-08"
}
```

`chain` is the artifact that gets hashed. `leaf_preimage` sits outside that hash
so a verifier can recompute `chain.leaf_action_ref` independently. The inner
`delegation_chain_ref` is the primitive's own field name, kept unchanged.

## Invariants checked

Taken unmodified from giskard09/argentum-core at `16e140a`, in that order:

0. **content address** - `SHA-256(JCS(chain))` equals the declared `delegation_chain_ref`
1. **chain continuity** - `hops[i].delegatee == hops[i+1].delegator` for all `i`
2. **root anchoring** - `chain.root_delegator == hops[0].delegator`
3. **leaf anchoring** - `action_ref` recomputed from `leaf_preimage` equals
   `chain.leaf_action_ref`, and `leaf_preimage.scope == hops[-1].scope`
4. **monotonic scope narrowing** - each hop scope equals its parent, or is a
   sub-namespace of it under the `:` separator; a parent ending in `:*` matches
   any child under the prefix before the star

Minimum chain length is two hops, per `delegation-chain-ref.md` invariant 6.

## Composition rule - `AND_PRESENT`

```
verdicts = [v.verdict for v in (v_gate, v_gate_skill, screen_ref, delegation_chain_ref) if v is not None]
composed_decision = "act" if verdicts and all(v == "act" for v in verdicts) else "halt"
```

Unchanged from v0.3-composed; it now folds the chain verdict as a fourth term.
Absent sibling pointers do not contribute. Any present-and-halt collapses the
composed decision to halt. Empty composition fails closed.

## Running the verifiers

```sh
# Node (verify.mjs)
node verify.mjs

# Python (verify.py)
python3 verify.py
```

Both must print byte-identical output:

```
PASS: 3 vectors (1 accept verified end-to-end, 2 reject correctly refused)
```

Dependency profiles are identical to the v0.3-composed pair: `verify.mjs` uses
Node built-ins only, `verify.py` uses the standard library plus `cryptography`.
Each vendors its own RFC 8785 (JCS) serializer, so a parity pass means the
canonical bytes, the chain and leaf recomputations, the AND_PRESENT outcome and
the Ed25519 signature checks all agree across two language runtimes.

## Regenerating

```sh
python3 build_fixtures.py
```

Keys are derived deterministically from labeled seeds, so a rebuild reproduces
every byte. All key material here is test-only fixture material and is not
reused from any deployed system.

## v0.3-composed vs v0.4-composed

| Aspect                          | v0.3-composed (Phase 1 + Phase 2)              | v0.4-composed (Phase 3)                              |
|---------------------------------|------------------------------------------------|------------------------------------------------------|
| Signers                         | AgentOracle, AgentTrust, Presidio              | + Argentum                                           |
| Sibling pointers                | `v_gate`, `v_gate_skill`, `screen_ref`         | + `delegation_chain_ref`                              |
| Question answered               | Was the action safe to take                    | + was the authority to take it validly delegated     |
| Recomputed content addresses    | `screen_ref.action_ref`                        | + the chain ref and `chain.leaf_action_ref`           |
| Decision rule                   | `AND_PRESENT`                                  | `AND_PRESENT` (unchanged, now folds the chain verdict)|

The v0.3-composed suite is not modified by Phase 3. Its vector ids, kids,
mapping hashes and fixture bytes are unchanged.

## Known gap, carried from upstream

`delegation-chain-ref-v1` at `16e140a` specifies no per-hop principal-signature
scheme: each hop carries a `delegation_ref` content address, and nothing binds a
hop to a key held by its delegator. This suite does not add one. Authentication
here comes from the JWS signatures over the composed payload, which cover the
envelope rather than the individual hops.
