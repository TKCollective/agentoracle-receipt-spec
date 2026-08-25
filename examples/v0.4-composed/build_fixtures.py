#!/usr/bin/env python3
"""Build fixture artifacts for verification.v0.4+composed envelope.

Produces:
  jwks-agentoracle.json, jwks-agenttrust.json, jwks-presidio.json, jwks-argentum.json
  payload-008.json, jws-008.json                        (accept vector)
  payload-r05.json, jws-r05.json, payload-r06.json, jws-r06.json  (reject vectors)
  vectors.json (the manifest the verifiers consume)

All keys are derived deterministically from labeled seeds so the suite is
byte-reproducible across machines. Keys are test-only fixture material and are
not reused from any deployed system.

Composed envelope shape (verification.v0.4+composed, Phase 3 = AO + AT + Presidio
+ Argentum signers):
  - subject (claim hashes)
  - v_gate (AgentOracle pre-action verdict)
  - v_gate_skill (AgentTrust skill/MCP/endpoint scan verdict)
  - screen_ref (Presidio PII-screening verdict, action-ref-v1 content address)
  - delegation_chain_ref (Argentum multi-hop authority chain,
    delegation-chain-ref-v1 content address) -- the Phase 3 addition
  - composed_decision + composed_decision_rule (AND_PRESENT, unchanged)
  - signature_meta (issuer JWKS URLs)
  - mycelium_trail_id ABSENT (not null) unless the run resolves a trail

delegation_chain_ref answers authority provenance: was the multi-hop chain from
root delegator to leaf agent valid. It never answers action identity, and it
never enters any action_ref preimage (delegation-chain-ref.md invariant 4).
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
)


HERE = Path(__file__).parent
ENVELOPE_KIND = "verification.v0.4+composed"
JWS_TYP = "application/vnd.verification.v0.4+composed+jws"


def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def b64u_json(obj: Any) -> str:
    # Headers use compact JSON; whitespace stripped. Header is not JCS-canonical.
    return b64u(json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def derive_ed25519_key(label: str) -> Ed25519PrivateKey:
    seed = hashlib.sha256(f"agentoracle-receipt-spec::v0.4-composed::{label}".encode("utf-8")).digest()
    return Ed25519PrivateKey.from_private_bytes(seed)


def jwk_from_public(pub: Ed25519PublicKey, kid: str) -> dict:
    raw = pub.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return {"kty": "OKP", "crv": "Ed25519", "kid": kid, "use": "sig", "alg": "EdDSA", "x": b64u(raw)}


# ----------------------------------------------------------------------------
# JCS (RFC 8785) canonicalization
# ----------------------------------------------------------------------------
# Carried over unchanged from v0.3-composed/build_fixtures.py so the two suites
# produce identical canonical bytes for identical input:
#   - Strings (RFC 8785 3.2.2.2): ECMAScript JSON.stringify minimal escapes
#   - Numbers (RFC 8785 3.2.2.3): ECMAScript Number.prototype.toString
#   - Objects: keys sorted by UTF-16 code units (BMP-only, matches code points)
#   - Arrays: order preserved
#   - true / false / null literal


def _jcs_string(s: str) -> str:
    out = ['"']
    for ch in s:
        cp = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\b":
            out.append("\\b")
        elif ch == "\f":
            out.append("\\f")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif cp < 0x20:
            out.append(f"\\u{cp:04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _jcs_number(n: int | float) -> str:
    if isinstance(n, bool):
        raise TypeError("bool must serialize as true/false, not number")
    if isinstance(n, int):
        return str(n)
    if not isinstance(n, float):
        raise TypeError(f"unsupported number type: {type(n)}")
    if n != n or n in (float("inf"), float("-inf")):
        raise ValueError("non-finite numbers forbidden in JCS")
    if n == 0:
        return "0"
    return repr(n)


def jcs(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, str):
        return _jcs_string(value)
    if isinstance(value, (int, float)):
        return _jcs_number(value)
    if isinstance(value, list):
        return "[" + ",".join(jcs(v) for v in value) + "]"
    if isinstance(value, dict):
        keys = sorted(value.keys(), key=lambda k: k.encode("utf-16-be"))
        return "{" + ",".join(_jcs_string(k) + ":" + jcs(value[k]) for k in keys) + "}"
    raise TypeError(f"unsupported JCS type: {type(value)}")


# ----------------------------------------------------------------------------
# Key material -- deterministic, test-only
# ----------------------------------------------------------------------------

AO_KID = "ao-fixture-v0.4-composed-2026-08"
AT_KID = "at-fixture-v0.4-composed-2026-08"
PRESIDIO_KID = "presidio-fixture-v0.4-composed-2026-08"
# Phase 3 -- Argentum delegation_chain_ref signer (additive fourth leg).
ARGENTUM_KID = "argentum-fixture-v0.4-composed-2026-08"

ao_sk = derive_ed25519_key("agentoracle-issuer-v1")
ao_pk = ao_sk.public_key()
at_sk = derive_ed25519_key("agenttrust-issuer-v1")
at_pk = at_sk.public_key()
presidio_sk = derive_ed25519_key("presidio-issuer-v1")
presidio_pk = presidio_sk.public_key()
argentum_sk = derive_ed25519_key("argentum-issuer-v1")
argentum_pk = argentum_sk.public_key()

jwks_ao = {"keys": [jwk_from_public(ao_pk, AO_KID)]}
jwks_at = {"keys": [jwk_from_public(at_pk, AT_KID)]}
jwks_presidio = {"keys": [jwk_from_public(presidio_pk, PRESIDIO_KID)]}
jwks_argentum = {"keys": [jwk_from_public(argentum_pk, ARGENTUM_KID)]}

(HERE / "jwks-agentoracle.json").write_text(json.dumps(jwks_ao, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(HERE / "jwks-agenttrust.json").write_text(json.dumps(jwks_at, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(HERE / "jwks-presidio.json").write_text(json.dumps(jwks_presidio, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(HERE / "jwks-argentum.json").write_text(json.dumps(jwks_argentum, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# ----------------------------------------------------------------------------
# Issuer metadata
# ----------------------------------------------------------------------------

AO_MAPPING_ID = "agentoracle-v0.3-2026-05-30"
AO_MAPPING_HASH = "sha256-0a78263976790df6e76cd9f3f441bf5a3b5c3a82e346b5aca43e49626881d7b0"
AT_MAPPING_ID = "agenttrust-v0.3-2026-06-07"
AT_MAPPING_HASH = "sha256-307db9faa364cfe149fb5120d0451175175de40d7433c44915bfec57acc16ec4"
PRESIDIO_MAPPING_ID = "presidio-x402-screen-v0.1-2026-06"
ARGENTUM_MAPPING_ID = "argentum-delegation-chain-v0.1-2026-08"

AO_JWKS_URL = "https://agentoracle.co/.well-known/jwks.json"
AT_JWKS_URL = "https://agenttrust.uk/.well-known/jwks.json"
PRESIDIO_JWKS_URL = "https://screen.presidio-group.eu/.well-known/jwks.json"
# Host as declared in giskard09/argentum-core docs/mycelium-provider-protocol.md.
ARGENTUM_JWKS_URL = "https://argentum-api.rgiskard.xyz/.well-known/jwks.json"

SIGMETA_P3 = {
    "agentoracle_jwks_url": AO_JWKS_URL,
    "agenttrust_jwks_url": AT_JWKS_URL,
    "presidio_jwks_url": PRESIDIO_JWKS_URL,
    "argentum_jwks_url": ARGENTUM_JWKS_URL,
    "signing_trust_ref": "signing-trust-ref-v1:str-003",
}


# ----------------------------------------------------------------------------
# action-ref-v1 and delegation-chain-ref-v1 derivations
# ----------------------------------------------------------------------------
# Both are lowercase-hex SHA-256 over RFC 8785 JCS canonical bytes. action_ref
# covers the four-field preimage {agent_id, action_type, scope, timestamp};
# delegation_chain_ref covers the chain artifact. Neither derivation is modified
# here and no field is added to any action_ref preimage.


def action_ref_of(preimage: dict) -> str:
    """action-ref-v1: lowercase-hex SHA-256 of the JCS canonical 4-field preimage."""
    return hashlib.sha256(jcs(preimage).encode("utf-8")).hexdigest()


def delegation_chain_ref_of(chain_artifact: dict) -> str:
    """delegation-chain-ref-v1: lowercase-hex SHA-256 of JCS(chain_artifact).

    Per giskard09/argentum-core docs/spec/delegation-chain-ref.md at 16e140a.
    """
    return hashlib.sha256(jcs(chain_artifact).encode("utf-8")).hexdigest()


# ----------------------------------------------------------------------------
# Phase 3 -- delegation_chain_ref leg (additive fourth sibling pointer + signer)
# ----------------------------------------------------------------------------
# Test-only agent identities, scoped to this fixture suite. They are not reused
# from any deployed system and not reused from the argentum-core fixture set.

ROOT_DELEGATOR = "did:x402:fixture:treasury-root"
BROKER_AGENT = "did:x402:fixture:broker-agent"
SETTLEMENT_AGENT = "did:x402:fixture:settlement-agent"
ROGUE_AGENT = "did:x402:fixture:rogue-agent"

# Per-hop delegation_ref values are content addresses of the delegation
# artifacts that authorized each hop, derived per argentum-core
# docs/spec/delegation-ref.md. This suite carries the chain, not the individual
# delegation artifacts, so each delegation_ref is a fixed test-only digest
# derived from a labeled seed. Deterministic so the suite rebuilds byte-identically.


def fixture_delegation_ref(label: str) -> str:
    return hashlib.sha256(f"agentoracle-receipt-spec::v0.4-composed::delegation-ref::{label}".encode("utf-8")).hexdigest()


def chain_block(
    *,
    chain_id: str,
    hops: list[dict],
    leaf_preimage: dict,
    verdict: str,
) -> dict:
    """Build the delegation_chain_ref sibling pointer.

    chain is the artifact that gets hashed; leaf_preimage sits outside the hash
    so a verifier can recompute chain.leaf_action_ref from it. The inner field
    name delegation_chain_ref is the primitive's own field name, kept unchanged.
    """
    chain_artifact = {
        "chain_id": chain_id,
        "hops": hops,
        "leaf_action_ref": action_ref_of(leaf_preimage),
        "root_delegator": hops[0]["delegator"],
        "scope": hops[0]["scope"],
        "version": "delegation-chain-ref-v1",
    }
    return {
        "issuer": "argentum",
        "verdict": verdict,
        "chain": chain_artifact,
        "leaf_preimage": leaf_preimage,
        "delegation_chain_ref": delegation_chain_ref_of(chain_artifact),
        "mapping_id": ARGENTUM_MAPPING_ID,
    }


def hop(delegator: str, delegatee: str, scope: str, label: str) -> dict:
    return {
        "delegatee": delegatee,
        "delegator": delegator,
        "delegation_ref": fixture_delegation_ref(label),
        "scope": scope,
    }


# ----------------------------------------------------------------------------
# screen_ref -- carried forward unchanged from v0.3-composed Phase 2
# ----------------------------------------------------------------------------
# Byte-identical to the Phase 2 SR_003 block, which is itself byte-identical to
# argentum-core conformance vector presidio-x402-003. Phase 3 does not touch
# screen_ref or action_ref handling; the block is present so the envelope
# exercises all four siblings under AND_PRESENT.

SCREEN_003 = {
    "agent_id": "did:presidio:x402:agent-7f3a9c",
    "action_type": "pii_screen",
    "scope": "presidio:x402.screen:PII_REDACTED:EMAIL_ADDRESS,US_SSN",
    "timestamp": "2026-06-20T17:45:00.000Z",
}
SCREEN_REF_003 = {
    "issuer": "presidio",
    "verdict": "act",
    "screen": SCREEN_003,
    "action_ref": action_ref_of(SCREEN_003),
    "mapping_id": PRESIDIO_MAPPING_ID,
}
# Enforce the cross-link to the published argentum-core target at build time.
# An explicit raise, not assert: assert is stripped under `python -O`.
if SCREEN_REF_003["action_ref"] != "c832ef8610c6989f8c6f5cea51ac019b8ac9860e389110079a895e67595950a2":
    raise ValueError(f"screen_ref drift: {SCREEN_REF_003['action_ref']}")


# ----------------------------------------------------------------------------
# Payloads
# ----------------------------------------------------------------------------


def base_payload(*, claim: str, skill: str, chain_ref_block: dict) -> dict:
    payload = {
        "receipt_version": "0.4.0-composed",
        "envelope_kind": ENVELOPE_KIND,
        "subject": {
            "claim_hash": "sha256-" + hashlib.sha256(claim.encode("utf-8")).hexdigest(),
            "skill_hash": "sha256-" + hashlib.sha256(skill.encode("utf-8")).hexdigest(),
        },
        "v_gate": {
            "issuer": "agentoracle",
            "verdict": "act",
            "v_confidence": 0.87,
            "v_gate_threshold": 0.7,
            "v_adversarial_result": "resilient",
            "v_recommendation": "confident_supported",
            "mapping_id": AO_MAPPING_ID,
            "v_gate_mapping_hash": AO_MAPPING_HASH,
        },
        "v_gate_skill": {
            "issuer": "agenttrust",
            "verdict": "act",
            "skill_results": [{"name": "x402.settle", "status": "clean"}],
            "mcp_results": [],
            "endpoint_results": [],
            "mapping_id": AT_MAPPING_ID,
            "v_gate_mapping_hash": AT_MAPPING_HASH,
        },
        "composed_decision": "act",
        "composed_decision_rule": "AND_PRESENT",
        "signature_meta": SIGMETA_P3,
        "screen_ref": SCREEN_REF_003,
        "delegation_chain_ref": chain_ref_block,
    }
    verdicts = [
        payload["v_gate"]["verdict"],
        payload["v_gate_skill"]["verdict"],
        payload["screen_ref"]["verdict"],
        payload["delegation_chain_ref"]["verdict"],
    ]
    payload["composed_decision"] = "act" if all(v == "act" for v in verdicts) else "halt"
    return payload


def make_protected(kid: str) -> dict:
    return {"alg": "EdDSA", "kid": kid, "typ": JWS_TYP}


def sign_compose(payload: dict, *, signers: list[tuple[Ed25519PrivateKey, str]]) -> dict:
    """Return JWS general serialization with N signatures over the JCS canonical payload."""
    canonical = jcs(payload).encode("utf-8")
    payload_b64 = b64u(canonical)
    signatures = []
    for sk, kid in signers:
        protected_b64 = b64u_json(make_protected(kid))
        signing_input = (protected_b64 + "." + payload_b64).encode("ascii")
        signatures.append({"protected": protected_b64, "signature": b64u(sk.sign(signing_input))})
    return {"payload": payload_b64, "signatures": signatures}


P3_SIGNERS = [(ao_sk, AO_KID), (at_sk, AT_KID), (presidio_sk, PRESIDIO_KID), (argentum_sk, ARGENTUM_KID)]

LEAF_TS = "2026-08-24T12:00:00.000Z"


# ----------------------------------------------------------------------------
# comp-008 -- accept. Valid two-hop chain, monotonic narrowing.
# ----------------------------------------------------------------------------
# x402:* narrows to x402:payment. Two hops is the minimum chain length the
# primitive defines (delegation-chain-ref.md invariant 6). Root anchoring holds,
# leaf_action_ref recomputes from leaf_preimage, and leaf_preimage.scope equals
# hops[-1].scope.

CHAIN_008 = chain_block(
    chain_id="chain-x402-settle-008",
    hops=[
        hop(ROOT_DELEGATOR, BROKER_AGENT, "x402:*", "008-hop0"),
        hop(BROKER_AGENT, SETTLEMENT_AGENT, "x402:payment", "008-hop1"),
    ],
    leaf_preimage={
        "agent_id": SETTLEMENT_AGENT,
        "action_type": "payment.settle",
        "scope": "x402:payment",
        "timestamp": LEAF_TS,
    },
    verdict="act",
)
P008 = base_payload(
    claim="Settlement of x402 invoice INV-2026-08-24-001 for 12.50 USDC.",
    skill="x402.settle",
    chain_ref_block=CHAIN_008,
)

# ----------------------------------------------------------------------------
# comp-r05 -- reject. One hop widens scope relative to its parent.
# ----------------------------------------------------------------------------
# hops[0].scope is x402:payment and hops[1].scope is x402:*, which is broader.
# Everything else stays valid so the reject isolates narrowing: root anchoring
# holds, the chain content address matches, chain continuity holds, and
# leaf_preimage.scope still equals hops[-1].scope so leaf anchoring passes.

CHAIN_R05 = chain_block(
    chain_id="chain-x402-settle-r05",
    hops=[
        hop(ROOT_DELEGATOR, BROKER_AGENT, "x402:payment", "r05-hop0"),
        hop(BROKER_AGENT, SETTLEMENT_AGENT, "x402:*", "r05-hop1"),
    ],
    leaf_preimage={
        "agent_id": SETTLEMENT_AGENT,
        "action_type": "payment.settle",
        "scope": "x402:*",
        "timestamp": LEAF_TS,
    },
    verdict="act",
)
P_R05 = base_payload(
    claim="Reject vector: delegation chain widens scope at hop 1.",
    skill="x402.settle",
    chain_ref_block=CHAIN_R05,
)

# ----------------------------------------------------------------------------
# comp-r06 -- reject. Chain continuity broken.
# ----------------------------------------------------------------------------
# hops[0].delegatee is the broker agent but hops[1].delegator is a different
# agent, so the chain does not link. Everything else stays valid so the reject
# isolates continuity: narrowing still holds (x402:* narrows to x402:payment),
# root anchoring holds, the content address matches, and leaf anchoring passes.

CHAIN_R06 = chain_block(
    chain_id="chain-x402-settle-r06",
    hops=[
        hop(ROOT_DELEGATOR, BROKER_AGENT, "x402:*", "r06-hop0"),
        hop(ROGUE_AGENT, SETTLEMENT_AGENT, "x402:payment", "r06-hop1"),
    ],
    leaf_preimage={
        "agent_id": SETTLEMENT_AGENT,
        "action_type": "payment.settle",
        "scope": "x402:payment",
        "timestamp": LEAF_TS,
    },
    verdict="act",
)
P_R06 = base_payload(
    claim="Reject vector: delegation chain continuity broken at hop 1.",
    skill="x402.settle",
    chain_ref_block=CHAIN_R06,
)


# ----------------------------------------------------------------------------
# Write fixtures
# ----------------------------------------------------------------------------

accept_vectors = []
reject_vectors = []

canonical_008 = jcs(P008).encode("utf-8")
jws_008 = sign_compose(P008, signers=P3_SIGNERS)
(HERE / "payload-008.json").write_text(json.dumps(P008, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(HERE / "jws-008.json").write_text(json.dumps(jws_008, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
accept_vectors.append({
    "id": "comp-008",
    "description": "Four-signer: AO act + AT act + Presidio act + Argentum act over a valid two-hop delegation chain (x402:* narrows to x402:payment). Root anchoring holds and leaf_action_ref recomputes from leaf_preimage, so composed act.",
    "payload_file": "payload-008.json",
    "jws_file": "jws-008.json",
    "expected_canonical_sha256": "sha256-" + hashlib.sha256(canonical_008).hexdigest(),
    "expected_composed_decision": P008["composed_decision"],
    "signer_kids": [AO_KID, AT_KID, PRESIDIO_KID, ARGENTUM_KID],
    "screen_ref_present": True,
    "screen_ref_action_ref": P008["screen_ref"]["action_ref"],
    "delegation_chain_ref_present": True,
    "delegation_chain_ref": P008["delegation_chain_ref"]["delegation_chain_ref"],
    "mycelium_trail_id_present": False,
})

for vid, payload, desc, failure, layer in [
    (
        "comp-r05", P_R05,
        "delegation_chain_ref hop 1 widens scope: hops[0].scope is x402:payment and hops[1].scope is x402:* , which is broader. Verifiers MUST enforce monotonic narrowing per argentum-core delegation-chain-ref-v1 (failure_mode scope_widening) and reject. Root anchoring, chain continuity, the chain content address, and leaf anchoring all remain valid so the reject isolates narrowing.",
        "delegation_chain_ref_scope_widening", "delegation_chain_narrowing",
    ),
    (
        "comp-r06", P_R06,
        "delegation_chain_ref chain continuity broken: hops[0].delegatee does not equal hops[1].delegator. Verifiers MUST enforce continuity per argentum-core delegation-chain-ref-v1 (failure_mode chain_break) and reject. Monotonic narrowing, root anchoring, the chain content address, and leaf anchoring all remain valid so the reject isolates continuity.",
        "delegation_chain_ref_chain_break", "delegation_chain_continuity",
    ),
]:
    num = vid.split("-")[1]
    jws = sign_compose(payload, signers=P3_SIGNERS)
    (HERE / f"payload-{num}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (HERE / f"jws-{num}.json").write_text(json.dumps(jws, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    reject_vectors.append({
        "id": vid,
        "description": desc,
        "payload_file": f"payload-{num}.json",
        "jws_file": f"jws-{num}.json",
        "expected_failure": failure,
        "failure_layer": layer,
    })


# ----------------------------------------------------------------------------
# vectors.json manifest
# ----------------------------------------------------------------------------

PHASE_NOTE = (
    "Phase 3 adds Argentum (delegation_chain_ref) as an additive fourth sibling pointer + "
    "signature on top of the byte-stable v0.3-composed suite, which is untouched: every "
    "v0.3 fixture, key, and manifest entry is unchanged byte-for-byte and this suite ships "
    "in its own directory. delegation_chain_ref is a delegation-chain-ref-v1 content "
    "address over a multi-hop authority chain; its block carries the chain artifact and the "
    "leaf preimage so verifiers recompute the chain ref and the leaf action_ref rather than "
    "trust them. It answers authority provenance (was the chain from root delegator to leaf "
    "agent valid) and never action identity; per delegation-chain-ref.md invariant 4 it is "
    "envelope-only and never enters an action_ref preimage. The primitive and its four "
    "invariants (chain continuity, root anchoring, leaf anchoring, monotonic scope "
    "narrowing) are taken from giskard09/argentum-core at 16e140a, unmodified and not "
    "renamed. Scope is three vectors: comp-008 accepts a narrowing chain, comp-r05 rejects "
    "a widening hop, comp-r06 rejects a continuity break. AND_PRESENT is unchanged and now "
    "folds the chain verdict."
)

suite = {
    "suite": "verification.v0.4+composed",
    "version": "v0.4-composed-phase-3",
    "spec": "../../README.md (Mycelium Trails section) + IETF draft-krausz-verification-state-01 + signing-trust-ref-v1 + action-ref-v1 (argentum-core action-ref.md @16dbc92) + delegation-chain-ref-v1 (argentum-core delegation-chain-ref.md @16e140a)",
    "phase": 3,
    "phase_note": PHASE_NOTE,
    "composition_rule": "AND_PRESENT",
    "composition_rule_note": "composed_decision = AND across all present sibling-pointer verdicts. Absent siblings do not contribute; any present-and-halt collapses the composed decision to halt.",
    "envelope_kind": ENVELOPE_KIND,
    "jws_typ": JWS_TYP,
    "signature_algorithm": "EdDSA (Ed25519)",
    "canonicalization": "RFC 8785 (JCS)",
    "issuers": [
        {"role": "v_gate", "issuer": "agentoracle", "jwks_file": "jwks-agentoracle.json", "jwks_url": AO_JWKS_URL, "kid": AO_KID, "mapping_id": AO_MAPPING_ID, "mapping_hash": AO_MAPPING_HASH},
        {"role": "v_gate_skill", "issuer": "agenttrust", "jwks_file": "jwks-agenttrust.json", "jwks_url": AT_JWKS_URL, "kid": AT_KID, "mapping_id": AT_MAPPING_ID, "mapping_hash": AT_MAPPING_HASH},
        {"role": "screen_ref", "issuer": "presidio", "jwks_file": "jwks-presidio.json", "jwks_url": PRESIDIO_JWKS_URL, "kid": PRESIDIO_KID, "mapping_id": PRESIDIO_MAPPING_ID, "spec": "argentum-core action-ref.md @16dbc92 (action-ref-v1)"},
        {"role": "delegation_chain_ref", "issuer": "argentum", "jwks_file": "jwks-argentum.json", "jwks_url": ARGENTUM_JWKS_URL, "kid": ARGENTUM_KID, "mapping_id": ARGENTUM_MAPPING_ID, "spec": "argentum-core delegation-chain-ref.md @16e140a (delegation-chain-ref-v1)"},
    ],
    "accept_vectors": accept_vectors,
    "reject_vectors": reject_vectors,
}

(HERE / "vectors.json").write_text(json.dumps(suite, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"Wrote {len(accept_vectors)} accept + {len(reject_vectors)} reject vectors")
for v in accept_vectors:
    print(f"  {v['id']}: composed_decision={v['expected_composed_decision']}  canonical_sha256={v['expected_canonical_sha256'][:24]}...")
    print(f"           delegation_chain_ref={v['delegation_chain_ref']}")
for v in reject_vectors:
    print(f"  {v['id']}: REJECT: {v['expected_failure']}")
