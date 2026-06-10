// build-aar-fixtures.mjs
// Builds composition_ref envelopes that wrap AgentOracle v0.3 JWS receipts
// inside metadata.domain_verdicts, per the integration shape outlined by
// @Liuyanfeng1234 in microsoft/autogen#7353.
//
// Output:
//   - composition-ref-allow.json   (composition_ref carrying AgentOracle ACT receipt)
//   - composition-ref-halt.json    (composition_ref carrying AgentOracle HALT receipt)
//
// composition_ref hash format (per giskard09/argentum-core#10):
//   raw = "action:{action_ref}|delegation:{delegation_ref}|revocation:{revocation_ref}|meta:{json(metadata)}|key_src:{key_source}|auth_ts:{ms}|revoke_ts:{ms}|ts:{ms}"
//   composition_ref = SHA-256(raw).hexdigest()[:16]
//
// We compute the composition_ref on our side and write it into each output
// file so giskard09/Liuyanfeng1234 can run the same inputs through their
// CompositionRefBuilder and confirm the hashes match.

import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const OUT = dirname(fileURLToPath(import.meta.url));
const V03 = join(OUT, '..', '..');

// Stable timestamps so the fixture is reproducible.
const AUTH_TS_MS = 1717804800000;       // 2026-06-08T00:00:00Z (matches receipt issued_at)
const REVOKE_TS_MS = 1717804800500;     // 500ms after authority verified
const COMPOSITION_TS_MS = 1717804801000; // composition built 1s after authority verified

const MAPPING_ID = 'v0.3.0-2026-05-30';
const MAPPING_HASH = 'sha256-02d91ee4e9f92efbb6a7218d13f726f400bf48bed79d7e4050e4ee8cd98bc0c1';
const REVIEWER_KID = 'ao-fixture-2026-06-v03-ed25519';
const JWKS_URI = 'https://agentoracle.co/.well-known/jwks.json';

// ---------- Helpers ----------------------------------------------------------

// Canonical JSON: sorted keys, no whitespace, UTF-8.
// We use this for the embedded metadata, matching the convention in
// argentum-core#10's "json(metadata)" embedding inside the pipe-separated raw.
function canonicalJSON(obj) {
  if (obj === null || typeof obj !== 'object') {
    return JSON.stringify(obj);
  }
  if (Array.isArray(obj)) {
    return '[' + obj.map(canonicalJSON).join(',') + ']';
  }
  const keys = Object.keys(obj).sort();
  return '{' + keys.map(k => JSON.stringify(k) + ':' + canonicalJSON(obj[k])).join(',') + '}';
}

function compositionRefHash({ action_ref, delegation_ref, revocation_ref, metadata, key_source, auth_ts_ms, revoke_ts_ms, ts_ms }) {
  const raw = `action:${action_ref}|delegation:${delegation_ref}|revocation:${revocation_ref}|meta:${canonicalJSON(metadata)}|key_src:${key_source}|auth_ts:${auth_ts_ms}|revoke_ts:${revoke_ts_ms}|ts:${ts_ms}`;
  return createHash('sha256').update(raw, 'utf8').digest('hex').slice(0, 16);
}

// ---------- Inputs -----------------------------------------------------------

const canonicalInput = JSON.parse(
  readFileSync(join(V03, 'canonical-input.json'), 'utf8')
);
const allowJws = JSON.parse(readFileSync(join(V03, 'receipt-allow.jws'), 'utf8'));
const haltJws = JSON.parse(readFileSync(join(V03, 'receipt-halt.jws'), 'utf8'));

// Decode each JWS payload to extract the verdict fields. The JWS in the
// fixture is in Flattened JSON form; the payload is base64url-encoded.
function decodePayload(jws) {
  const pad = '='.repeat((4 - (jws.payload.length % 4)) % 4);
  const b64 = jws.payload.replace(/-/g, '+').replace(/_/g, '/') + pad;
  return JSON.parse(Buffer.from(b64, 'base64').toString('utf8'));
}

const allowPayload = decodePayload(allowJws);
const haltPayload = decodePayload(haltJws);

// ---------- Build one composition_ref ----------------------------------------

function buildOne({ kind, jws, payload }) {
  // Map AgentOracle receipt fields into the domain_verdicts entry shape
  // sketched in microsoft/autogen#7353 by @Liuyanfeng1234:
  //   { claim_id, verdict, standard, reviewer }
  // We add standard_hash and the raw signed JWS so an auditor holding only
  // this composition_ref can independently verify the AgentOracle receipt.
  const domainVerdict = {
    claim_id: canonicalInput.subject.claim_hash,
    verdict: payload.v_recommendation,
    gate: payload.v_gate,
    standard: payload.v_gate_mapping,
    standard_hash: payload.v_gate_mapping_hash,
    reviewer: {
      jws_signer_kid: REVIEWER_KID,
      jwks_uri: JWKS_URI,
      receipt_typ: 'application/vnd.agentoracle.receipt+jws',
    },
    receipt_jws: jws,
  };

  // composition_ref fields (per argentum-core#10)
  const action_ref = `ao_action_${kind}_v03_demo_01`;
  const delegation_ref = 'ao_delegation_v03_demo_01';
  const revocation_ref = 'ao_revocation_v03_demo_01';
  const key_source = 'inline'; // jwks-fixture.json is bundled with the example
  const metadata = {
    domain_verdicts: [domainVerdict],
  };

  const composition_ref = compositionRefHash({
    action_ref,
    delegation_ref,
    revocation_ref,
    metadata,
    key_source,
    auth_ts_ms: AUTH_TS_MS,
    revoke_ts_ms: REVOKE_TS_MS,
    ts_ms: COMPOSITION_TS_MS,
  });

  return {
    spec: 'argentum-core/composition-ref-v1.0 + key_source (per argentum-core#10)',
    fields: {
      action_ref,
      delegation_ref,
      revocation_ref,
      metadata,
      key_source,
      authority_verified_at_ms: AUTH_TS_MS,
      revocation_check_at_ms: REVOKE_TS_MS,
      ts_ms: COMPOSITION_TS_MS,
    },
    computed: {
      composition_ref,
      hash_algorithm: 'SHA-256 (first 16 hex chars)',
      raw_format: 'action:{action_ref}|delegation:{delegation_ref}|revocation:{revocation_ref}|meta:{json(metadata)}|key_src:{key_source}|auth_ts:{ms}|revoke_ts:{ms}|ts:{ms}',
      canonical_metadata_json_preview: canonicalJSON(metadata).slice(0, 200) + '...',
    },
    cross_references: {
      ietf_draft: 'https://datatracker.ietf.org/doc/draft-krausz-verification-state/',
      ao_receipt_spec: 'https://github.com/TKCollective/agentoracle-receipt-spec/tree/v0.3-binary-halt',
      argentum_core_field_def: 'https://github.com/giskard09/argentum-core/issues/10',
      aar_thread: 'https://github.com/microsoft/autogen/issues/7353',
    },
  };
}

const allowOut = buildOne({ kind: 'allow', jws: allowJws, payload: allowPayload });
const haltOut = buildOne({ kind: 'halt', jws: haltJws, payload: haltPayload });

writeFileSync(join(OUT, 'composition-ref-allow.json'), JSON.stringify(allowOut, null, 2) + '\n');
writeFileSync(join(OUT, 'composition-ref-halt.json'), JSON.stringify(haltOut, null, 2) + '\n');

console.log('AAR fixtures written:');
console.log('  composition-ref-allow.json  composition_ref =', allowOut.computed.composition_ref, ' (v_gate=' + allowPayload.v_gate + ')');
console.log('  composition-ref-halt.json   composition_ref =', haltOut.computed.composition_ref, ' (v_gate=' + haltPayload.v_gate + ')');
console.log('');
console.log('Same canonical claim, same standard, same standard_hash, same timestamps.');
console.log('Differ only in: v_adversarial_result → v_recommendation → v_gate → embedded receipt_jws.');
