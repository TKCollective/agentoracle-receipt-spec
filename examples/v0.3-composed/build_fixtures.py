#!/usr/bin/env python3
"""Build fixture artifacts for verification.v0.3+composed envelope.

Produces:
  jwks-agentoracle.json, jwks-agenttrust.json
  payload-001.json ... payload-004.json (raw canonical payloads)
  jws-001.json ... jws-004.json (JWS general serialization, 2 signatures)
  jws-r01.json ... jws-r03.json (reject vectors)
  vectors.json (the manifest the verifiers consume)

All keys are derived deterministically from labeled seeds so the suite is
byte-reproducible across machines.

Composed envelope shape (verification.v0.3+composed, Phase 1 = AO + AT signers):
  - subject (claim hashes)
  - v_gate (AgentOracle pre-action verdict)
  - v_gate_skill (AgentTrust skill/MCP/endpoint scan verdict)
  - composed_decision + composed_decision_rule (AND_PRESENT)
  - signature_meta (issuer JWKS URLs)
  - screen_ref ABSENT in Phase 1 (Presidio leg additive in Phase 2)
  - mycelium_trail_id ABSENT (not null) in Phase 1 unless the run resolves a trail
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
    PrivateFormat,
    PublicFormat,
    NoEncryption,
)


HERE = Path(__file__).parent
ENVELOPE_KIND = "verification.v0.3+composed"
JWS_TYP = "application/vnd.verification.v0.3+composed+jws"


def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def b64u_json(obj: Any) -> str:
    # Headers use compact JSON; whitespace stripped. Header is not JCS-canonical —
    # it is the encoder's responsibility to produce identical bytes if recomputed.
    return b64u(json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def derive_ed25519_key(label: str) -> Ed25519PrivateKey:
    seed = hashlib.sha256(f"agentoracle-receipt-spec::v0.3-composed::{label}".encode("utf-8")).digest()
    return Ed25519PrivateKey.from_private_bytes(seed)


def jwk_from_public(pub: Ed25519PublicKey, kid: str) -> dict:
    raw = pub.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return {"kty": "OKP", "crv": "Ed25519", "kid": kid, "use": "sig", "alg": "EdDSA", "x": b64u(raw)}


# ----------------------------------------------------------------------------
# JCS (RFC 8785) canonicalization
# ----------------------------------------------------------------------------
# Scoped to the composed-envelope payload domain:
#   - Strings (RFC 8785 §3.2.2.2): ECMAScript JSON.stringify minimal escapes
#   - Numbers (RFC 8785 §3.2.2.3): ECMAScript Number.prototype.toString
#   - Objects: keys sorted by UTF-16 code units (BMP-only → matches code points)
#   - Arrays: order preserved
#   - true / false / null literal


def _jcs_string(s: str) -> str:
    # ECMAScript JSON.stringify: shortest form, two-char escapes for named
    # controls, \u00xx for the rest of C0; everything else literal.
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
    # ECMAScript Number.prototype.toString — Python's repr() matches for the
    # finite-precision values used in this fixture set. For 0.87, 0.7, etc.
    # repr() returns "0.87", "0.7" identical to JS Number.toString.
    if not isinstance(n, float):
        raise TypeError(f"unsupported number type: {type(n)}")
    if n != n or n in (float("inf"), float("-inf")):
        raise ValueError("non-finite numbers forbidden in JCS")
    if n == 0:
        return "0"
    # Python repr() agrees with JS toString for the values used here
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
        # Keys MUST be strings; sort by UTF-16 code units.
        keys = sorted(value.keys(), key=lambda k: k.encode("utf-16-be"))
        return "{" + ",".join(_jcs_string(k) + ":" + jcs(value[k]) for k in keys) + "}"
    raise TypeError(f"unsupported JCS type: {type(value)}")


# ----------------------------------------------------------------------------
# Key material — deterministic for reproducibility
# ----------------------------------------------------------------------------

AO_KID = "ao-fixture-v0.3-composed-2026-06"
AT_KID = "at-fixture-v0.3-composed-2026-06"

ao_sk = derive_ed25519_key("agentoracle-issuer-v1")
ao_pk = ao_sk.public_key()
at_sk = derive_ed25519_key("agenttrust-issuer-v1")
at_pk = at_sk.public_key()

jwks_ao = {"keys": [jwk_from_public(ao_pk, AO_KID)]}
jwks_at = {"keys": [jwk_from_public(at_pk, AT_KID)]}

(HERE / "jwks-agentoracle.json").write_text(json.dumps(jwks_ao, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(HERE / "jwks-agenttrust.json").write_text(json.dumps(jwks_at, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# ----------------------------------------------------------------------------
# Payloads
# ----------------------------------------------------------------------------

AO_MAPPING_ID = "agentoracle-v0.3-2026-05-30"
AO_MAPPING_HASH = "sha256-3b1f2d8e7a5c4b9f6e0a1d2c3b4a5e6f7c8d9e0a1b2c3d4e5f6a7b8c9d0e1f2a"
AT_MAPPING_ID = "agenttrust-v0.3-2026-06-07"
AT_MAPPING_HASH = "sha256-307db9faa364cfe149fb5120d0451175175de40d7433c44915bfec57acc16ec4"

AO_JWKS_URL = "https://agentoracle.co/.well-known/jwks.json"
AT_JWKS_URL = "https://agenttrust.uk/.well-known/jwks.json"

SIGMETA = {"agentoracle_jwks_url": AO_JWKS_URL, "agenttrust_jwks_url": AT_JWKS_URL}


def base_payload(idx: int, ao_verdict: str, at_verdict: str, *, claim: str, skill: str, trail_id: str | None = None) -> dict:
    payload = {
        "receipt_version": "0.3.0-composed",
        "envelope_kind": ENVELOPE_KIND,
        "subject": {
            "claim_hash": "sha256-" + hashlib.sha256(claim.encode("utf-8")).hexdigest(),
            "skill_hash": "sha256-" + hashlib.sha256(skill.encode("utf-8")).hexdigest(),
        },
        "v_gate": {
            "issuer": "agentoracle",
            "verdict": ao_verdict,
            "v_confidence": 0.87 if ao_verdict == "act" else 0.31,
            "v_gate_threshold": 0.7,
            "v_adversarial_result": "resilient" if ao_verdict == "act" else "vulnerable",
            "v_recommendation": "confident_supported" if ao_verdict == "act" else "refuted",
            "mapping_id": AO_MAPPING_ID,
            "v_gate_mapping_hash": AO_MAPPING_HASH,
        },
        "v_gate_skill": {
            "issuer": "agenttrust",
            "verdict": at_verdict,
            "skill_results": [{"name": "calendar.create_event", "status": "clean"}] if at_verdict == "act" else [{"name": "calendar.create_event", "status": "untrusted_origin"}],
            "mcp_results": [],
            "endpoint_results": [],
            "mapping_id": AT_MAPPING_ID,
            "v_gate_mapping_hash": AT_MAPPING_HASH,
        },
        "composed_decision": "act" if (ao_verdict == "act" and at_verdict == "act") else "halt",
        "composed_decision_rule": "AND_PRESENT",
        "signature_meta": SIGMETA,
    }
    if trail_id is not None:
        payload["mycelium_trail_id"] = trail_id
    return payload


# Phase 1 accept vectors
P001 = base_payload(1, "act", "act", claim="Bitcoin's price in USD on 2026-06-08 was $61,420.", skill="calendar.create_event")
P002 = base_payload(2, "act", "halt", claim="The mitochondrion is the powerhouse of the cell.", skill="mcp.tool_invoke")
P003 = base_payload(3, "halt", "act", claim="Treaty of Versailles was signed in 1820.", skill="ledger.append")
P004 = base_payload(4, "act", "act", claim="Patient John Doe has a documented penicillin allergy.", skill="healthcare.prescribe", trail_id="trail_demo_2026-06-22_001")


# ----------------------------------------------------------------------------
# Build JWS general serialization
# ----------------------------------------------------------------------------

def make_protected(kid: str) -> dict:
    return {"alg": "EdDSA", "kid": kid, "typ": JWS_TYP}


def sign_compose(payload: dict, *, signers: list[tuple[Ed25519PrivateKey, str]]) -> dict:
    """Return JWS general serialization with N signatures over the JCS canonical payload."""
    canonical = jcs(payload).encode("utf-8")
    payload_b64 = b64u(canonical)
    signatures = []
    for sk, kid in signers:
        protected = make_protected(kid)
        protected_b64 = b64u_json(protected)
        signing_input = (protected_b64 + "." + payload_b64).encode("ascii")
        sig = sk.sign(signing_input)
        signatures.append({"protected": protected_b64, "signature": b64u(sig)})
    return {"payload": payload_b64, "signatures": signatures}


vectors_accept = []
for idx, payload in enumerate([P001, P002, P003, P004], start=1):
    vid = f"comp-{idx:03d}"
    canonical_bytes = jcs(payload).encode("utf-8")
    canonical_hash = "sha256-" + hashlib.sha256(canonical_bytes).hexdigest()
    jws = sign_compose(payload, signers=[(ao_sk, AO_KID), (at_sk, AT_KID)])
    (HERE / f"payload-{idx:03d}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (HERE / f"jws-{idx:03d}.json").write_text(json.dumps(jws, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    vectors_accept.append({
        "id": vid,
        "description": {
            1: "Happy path — both issuers approve. No trail anchor.",
            2: "AgentOracle approves, AgentTrust halts on skill — composed halts.",
            3: "AgentTrust approves, AgentOracle refutes the claim — composed halts.",
            4: "Happy path with a resolved mycelium_trail_id present.",
        }[idx],
        "payload_file": f"payload-{idx:03d}.json",
        "jws_file": f"jws-{idx:03d}.json",
        "expected_canonical_sha256": canonical_hash,
        "expected_composed_decision": payload["composed_decision"],
        "signer_kids": [AO_KID, AT_KID],
        "screen_ref_present": False,
        "mycelium_trail_id_present": "mycelium_trail_id" in payload,
    })


# ----------------------------------------------------------------------------
# Reject vectors — each MUST fail verification for a documented reason
# ----------------------------------------------------------------------------

reject_vectors: list[dict] = []

# r01 — one signature valid, one tampered (single byte flip on AT signature)
P_R01 = base_payload(1, "act", "act", claim="Reject vector — tampered signature.", skill="calendar.create_event")
jws_r01 = sign_compose(P_R01, signers=[(ao_sk, AO_KID), (at_sk, AT_KID)])
# Flip last 4 chars of AT signature to invalidate it (still valid base64url, fails verify)
at_sig_b64 = jws_r01["signatures"][1]["signature"]
jws_r01["signatures"][1]["signature"] = at_sig_b64[:-4] + ("AAAA" if at_sig_b64[-4:] != "AAAA" else "BBBB")
(HERE / "payload-r01.json").write_text(json.dumps(P_R01, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(HERE / "jws-r01.json").write_text(json.dumps(jws_r01, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
reject_vectors.append({
    "id": "comp-r01",
    "description": "One signature valid, one signature tampered (AgentTrust signature corrupted). Entire envelope MUST reject.",
    "payload_file": "payload-r01.json",
    "jws_file": "jws-r01.json",
    "expected_failure": "signature_invalid",
    "failure_layer": "signature",
})

# r02 — mycelium_trail_id present but null (forbidden by the protocol)
P_R02 = base_payload(2, "act", "act", claim="Reject vector — mycelium_trail_id is null.", skill="calendar.create_event")
P_R02["mycelium_trail_id"] = None
jws_r02 = sign_compose(P_R02, signers=[(ao_sk, AO_KID), (at_sk, AT_KID)])
(HERE / "payload-r02.json").write_text(json.dumps(P_R02, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(HERE / "jws-r02.json").write_text(json.dumps(jws_r02, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
reject_vectors.append({
    "id": "comp-r02",
    "description": "mycelium_trail_id is null. Per the Mycelium Provider protocol (and the AgentOracle composed envelope spec) the field MUST be absent (not null) when /external/trail fails. Verifiers MUST reject envelopes whose mycelium_trail_id is null.",
    "payload_file": "payload-r02.json",
    "jws_file": "jws-r02.json",
    "expected_failure": "mycelium_trail_id_is_null",
    "failure_layer": "envelope_grammar",
})

# r03 — composed_decision violates AND_PRESENT (signed `act` over halt+act)
P_R03 = base_payload(3, "halt", "act", claim="Reject vector — composed_decision violates rule.", skill="calendar.create_event")
P_R03["composed_decision"] = "act"  # tampered — AND_PRESENT requires this to be 'halt'
jws_r03 = sign_compose(P_R03, signers=[(ao_sk, AO_KID), (at_sk, AT_KID)])
(HERE / "payload-r03.json").write_text(json.dumps(P_R03, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(HERE / "jws-r03.json").write_text(json.dumps(jws_r03, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
reject_vectors.append({
    "id": "comp-r03",
    "description": "composed_decision = 'act' but v_gate verdict is 'halt' — violates AND_PRESENT rule. Verifier MUST recompute composed_decision from the present sibling pointers and reject on mismatch with the signed value.",
    "payload_file": "payload-r03.json",
    "jws_file": "jws-r03.json",
    "expected_failure": "composed_decision_rule_violated",
    "failure_layer": "composition_rule",
})

# ----------------------------------------------------------------------------
# vectors.json manifest
# ----------------------------------------------------------------------------

suite = {
    "suite": "verification.v0.3+composed",
    "version": "v0.3-composed-phase-1",
    "spec": "../../README.md (Mycelium Trails section) + IETF draft-krausz-verification-state-01 + signing-trust-ref-v1 alignment (Phase 2)",
    "phase": 1,
    "phase_note": "Phase 1 ships two-signer JWS general serialization with AgentOracle (v_gate) and AgentTrust (v_gate_skill). screen_ref (Presidio) is absent — Phase 2 follow-on PR adds it as an additive third sibling pointer + signature. mycelium_trail_id is absent except where a trail resolves (vector comp-004); the field MUST be absent (not null) when /external/trail fails per giskard09/argentum-core/docs/mycelium-provider-protocol.md.",
    "composition_rule": "AND_PRESENT",
    "composition_rule_note": "composed_decision = AND across all present sibling-pointer verdicts. Absent siblings do not contribute; any present-and-halt collapses the composed decision to halt.",
    "envelope_kind": ENVELOPE_KIND,
    "jws_typ": JWS_TYP,
    "signature_algorithm": "EdDSA (Ed25519)",
    "canonicalization": "RFC 8785 (JCS)",
    "issuers": [
        {"role": "v_gate", "issuer": "agentoracle", "jwks_file": "jwks-agentoracle.json", "jwks_url": AO_JWKS_URL, "kid": AO_KID, "mapping_id": AO_MAPPING_ID, "mapping_hash": AO_MAPPING_HASH},
        {"role": "v_gate_skill", "issuer": "agenttrust", "jwks_file": "jwks-agenttrust.json", "jwks_url": AT_JWKS_URL, "kid": AT_KID, "mapping_id": AT_MAPPING_ID, "mapping_hash": AT_MAPPING_HASH},
    ],
    "accept_vectors": vectors_accept,
    "reject_vectors": reject_vectors,
}

(HERE / "vectors.json").write_text(json.dumps(suite, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"Wrote {len(vectors_accept)} accept + {len(reject_vectors)} reject vectors")
for v in vectors_accept:
    print(f"  {v['id']}: composed_decision={v['expected_composed_decision']}  canonical_sha256={v['expected_canonical_sha256'][:24]}...")
for v in reject_vectors:
    print(f"  {v['id']}: REJECT — {v['expected_failure']}")
