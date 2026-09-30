# Live receipts

Receipts issued by the production service, kept here so the bytes behind a published link cannot change. Each file is the `receipt.jws` object (the JWS envelope) from one response, nothing else. The signed payload carries a claim hash, not the claim text.

## evaluate-demo-2026-09-30.json

| Field | Value |
|---|---|
| Issued (payload `timestamp` / `v_gate.signed_at`) | `2026-09-30T02:37:01.475Z` |
| Signing key (`kid`) | `ao-composed-2026-06-ed25519-c3abfce3` |
| Canonical SHA-256 (RFC 8785 bytes of the payload) | `sha256-608f91ecf5f397dc1e02ed6dd1924288bb466dcff918c310f6abf29c91d308c9` |
| File SHA-256 | `4fd391e6dcd6844f12f0f94ea0a050ee7a52b851804ebcc41a914b31e1c2abb8` |
| Added in commit | `0f3b0cd8db5bb33c55aa73c1229c8398be96a37e` |

**How it was produced.** One `POST https://agentoracle.co/evaluate` with the body `{"content": "Paris is the capital of France."}`, made on 30 September 2026. The response reported `meta.cache_hit: false` and `meta.receipt_status: "signed"`, so the receipt comes from a fresh evaluation, not from the cache. Only the response's `receipt.jws` object was saved, as this file. The issue time above is the payload's own timestamp, not the requester's clock.

**Verify it offline.** The signature is checked against the published JWKS with no call to the service. Fetch the key set once, then verify:

```
pip install tanilo-receipt-verify==0.1.2
curl -s https://raw.githubusercontent.com/TKCollective/tanilo-receipt-spec/0f3b0cd8db5bb33c55aa73c1229c8398be96a37e/examples/live-receipts/evaluate-demo-2026-09-30.json -o receipt.json
curl -s https://agentoracle.co/.well-known/jwks.json -o jwks.json
python3 -c "import json; from tanilo_receipt_verify import verify; r=verify(json.load(open('receipt.json')), jwks_by_issuer={'https://agentoracle.co/.well-known/jwks.json': json.load(open('jwks.json'))}); print(r.status, r.canonical_sha256)"
```

Expected output:

```
valid sha256-608f91ecf5f397dc1e02ed6dd1924288bb466dcff918c310f6abf29c91d308c9
```

The file hash can be checked with `shasum -a 256 receipt.json`, which should print the file SHA-256 above.

**What the signature does and does not show.** A valid signature under `ao-composed-2026-06-ed25519-c3abfce3` proves the payload bytes have not changed since they were signed and that this published key signed them. It does not, on its own, prove the service issued the payload: from 23 June to 28 August 2026 the same key also signed bytes supplied by callers through routes that have since been closed, and a forged payload could carry any timestamp. What corroborates issuance is a check against the service's internal claim-fingerprint store, which the operator runs on request. See https://tanilo.io/incidents/2026-08-25-canned-verdicts.
