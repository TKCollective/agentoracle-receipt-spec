# AgentOracle Receipt Verification — Working Examples

End-to-end verifying examples for the receipt format described in the parent
[README](../README.md). Both examples fetch the live JWKS from the production
endpoint and verify a real detached JWS against a real payload.

**Live JWKS endpoint:** https://agentoracle.co/.well-known/jwks.json

## What's in this directory

| File | Purpose |
| --- | --- |
| `sample_payload.json` | Example `claim + evidence + confidence` payload — the canonical content the signature commits to |
| `sample_receipt_attached_jws.json` | Flattened JWS (attached payload) — used by the verifying examples for cross-language byte stability |
| `sample_receipt_detached_jws.json` | Flattened JWS (detached) — for reference; matches the production wire format |
| `verify_node.mjs` | Node.js verifier using [`jose`](https://github.com/panva/jose) |
| `verify_python.py` | Python verifier using [`joserfc`](https://github.com/authlib/joserfc) (EdDSA-supported; python-jose does not yet support EdDSA — [issue 319](https://github.com/mpdavis/python-jose/issues/319)) |
| `package.json` | Node deps (jose) |
| `requirements.txt` | Python deps (joserfc, requests) |

## Run the Node verifier

```bash
cd examples
npm install
node verify_node.mjs
```

Expected output:

```
=== VERIFIED OK ===
  algorithm:                EdDSA
  key id (kid):             ao-receipt-2026-04-ed25519-f2753b7c
  content type:             application/json
  receipt type:             application/vnd.agentoracle.receipt+jws
  jwks source:              https://agentoracle.co/.well-known/jwks.json
  ...
```

## Run the Python verifier

```bash
cd examples
pip install -r requirements.txt
python verify_python.py
```

Same expected output under `joserfc`.

> **Note on Python library choice:** `python-jose` is the historically popular
> JOSE library for Python but does not implement EdDSA / Ed25519
> ([issue 319](https://github.com/mpdavis/python-jose/issues/319), open since 2023).
> `joserfc` (Authlib) is RFC 7515 / 7517 / 8037-compliant and supports the
> full algorithm set. PyJWT also supports EdDSA via its OKP algorithm if a
> JWT-style API is preferred.

## Attached vs. detached

The production wire format is **detached** JWS (RFC 7797, `b64=false` flow) —
the receipt body transports the payload separately from the signature to
minimize header size on every `/evaluate` response.

The verifying examples here use the **attached** flattened form so the signature
covers exact bytes inside the JWS and there is zero canonicalization ambiguity
across languages. `sample_receipt_detached_jws.json` is included for spec
completeness; a detached-form verifier needs a byte-accurate canonical
serializer on both sides (issuer + verifier), which the attached form
side-steps by embedding the bytes directly.

## What you're seeing here

1. **The public key is live.** `GET https://agentoracle.co/.well-known/jwks.json`
   returns an RFC 7517 JWK Set with one Ed25519 key.
2. **The signature is real.** `sample_receipt_attached_jws.json` was signed
   with the matching private key. The private key lives only in the issuer
   environment; no test key or placeholder is used here.
3. **Standard libraries verify it.** Both `jose` (Node, 9k+ GitHub stars) and
   `joserfc` (Python, Authlib) verify cleanly with no custom parsing. If either
   example fails, the spec is wrong — this is the compliance test.

## Questions / PRs

Open an issue on this repo or join the
[Coinbase Developer Discord #x402 thread](https://discord.gg/cdp).
