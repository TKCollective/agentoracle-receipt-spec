"""generate_detached_fixture.py — Deterministic generator for the detached fixture.

Included for transparency and reproducibility. The signature is deterministic
given (fixture-key, protected-header, payload), so any implementer who runs
this against the committed fixture material should get byte-identical output
to sample_receipt_detached_jws.json in this directory.

Requires the same JCS + Ed25519 primitives as the verifier. Uses the private
half of ao-fixture-detached-rfc7797-2026-07-ed25519-* published in
jwks-fixture-detached.json.
"""
import base64, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

HERE = Path(__file__).parent
def b64u_enc(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def b64u_dec(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

_ESC = {'"':'\\"','\\':'\\\\','\b':'\\b','\f':'\\f','\n':'\\n','\r':'\\r','\t':'\\t'}
def _jcs_string(s):
    out=['"']
    for ch in s:
        if ch in _ESC: out.append(_ESC[ch])
        elif ord(ch)<0x20: out.append('\\u%04x'%ord(ch))
        else: out.append(ch)
    out.append('"'); return "".join(out)
def _jcs_number(x):
    if isinstance(x, bool): raise TypeError
    if isinstance(x, int): return str(x)
    if x != x or x in (float("inf"), float("-inf")): raise ValueError
    if x == int(x) and abs(x) < 1e21: return str(int(x))
    r = repr(x); assert float(r) == x and "e" not in r; return r
def jcs(o):
    if o is None: return "null"
    if o is True: return "true"
    if o is False: return "false"
    if isinstance(o, str): return _jcs_string(o)
    if isinstance(o, (int, float)): return _jcs_number(o)
    if isinstance(o, list): return "["+",".join(jcs(v) for v in o)+"]"
    if isinstance(o, dict):
        items=sorted(o.items(), key=lambda kv: kv[0].encode("utf-16-be"))
        return "{"+",".join(_jcs_string(k)+":"+jcs(v) for k,v in items)+"}"
    raise TypeError

priv = json.load(open(HERE / "jwks-fixture-detached.json"))["keys"][0]
sk = Ed25519PrivateKey.from_private_bytes(b64u_dec(priv["d"]))

header = {
    "alg": "EdDSA",
    "b64": False,
    "crit": ["b64"],
    "cty": "application/json",
    "kid": priv["kid"],
    "typ": "application/vnd.agentoracle.receipt+jws",
}
protected_b64 = b64u_enc(jcs(header).encode())
payload_bytes = jcs(json.load(open(HERE / "sample_payload.json"))).encode()
signing_input = protected_b64.encode("ascii") + b"." + payload_bytes
sig = sk.sign(signing_input)

with open(HERE / "sample_receipt_detached_jws.json", "w") as f:
    json.dump({"protected": protected_b64, "signature": b64u_enc(sig)}, f, indent=2)
    f.write("\n")
print("wrote sample_receipt_detached_jws.json")
