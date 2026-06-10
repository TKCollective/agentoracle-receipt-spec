// build-aar-fixtures.mjs (v2 — JCS migration)
//
// Builds composition_ref envelopes that wrap AgentOracle v0.3 JWS receipts
// inside metadata.domain_verdicts, per the integration shape outlined by
// @Liuyanfeng1234 in microsoft/autogen#7353.
//
// HASH FORMAT (per @Liuyanfeng1234's clarification, June 10):
// The authoritative composition_ref hash is SHA-256 over JCS canonical JSON
// (RFC 8785) of the full field set, taking the first 16 hex chars. The
// argentum-core#10 issue text describes a pipe-separated raw string format
// that PREDATES the JCS migration done in response to giskard09's review;
// it is no longer authoritative. CompositionRefBuilder now serializes via
// JCS and hashes the canonical bytes.
//
// Field set included in the JCS object (per Liuyanfeng's confirmation):
//   action_ref, delegation_ref, revocation_ref, key_source,
//   authority_verified_at_ms, revocation_check_at_ms, scope, version, metadata,
//   composition_built_at_ms

import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import canonicalize from 'canonicalize';

const OUT = dirname(fileURLToPath(import.meta.url));
const V03 = join(OUT, '..', '..');

// Stable timestamps so the fixture is reproducible.
const AUTH_TS_MS = 1717804800000;       // 2026-06-08T00:00:00Z (matches receipt issued_at)
const REVOKE_TS_MS = 1717804800500;     // 500ms after authority verified
const BUILD_TS_MS = 1717804801000;      // composition built 1s after authority verified

const REVIEWER_KID = 'ao-fixture-2026-06-v03-ed25519';
const JWKS_URI = 'https://agentoracle.co/.well-known/jwks.json';

// composition_ref schema version + per-action intent scope.
// `scope` and `version` were called out by @Liuyanfeng1234 as part of the
// fixed binding field set. The values here are the issuer's best guess; if
// CompositionRefBuilder expects different canonical values for either,
// flagging early so we converge on names rather than debug a hash mismatch.
const COMPOSITION_REF_VERSION = 'composition-ref-v1.0';
const ACTION_SCOPE = 'verification:factual_claim:pre_publish';

// ---------- Helpers ----------------------------------------------------------

// JCS RFC 8785 canonicalization. Using the `canonicalize` npm package, which is
// the reference implementation. This removes any ambiguity about whether the
// embedded metadata canonicalization or the whole-object canonicalization
// matches RFC 8785.
function jcs(obj) {
  return canonicalize(obj);
}

function compositionRefHash(fields) {
  // SHA-256 over JCS canonical bytes, first 16 hex chars.
  const canonical = jcs(fields);
  return createHash('sha256').update(canonical, 'utf8').digest('hex').slice(0, 16);
}

// ---------- Inputs -----------------------------------------------------------

const canonicalInput = JSON.parse(
  readFileSync(join(V03, 'canonical-input.json'), 'utf8')
);
const allowJws = JSON.parse(readFileSync(join(V03, 'receipt-allow.jws'), 'utf8'));
const haltJws = JSON.parse(readFileSync(join(V03, 'receipt-halt.jws'), 'utf8'));

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
  //   { claim_id, verdict, standard, reviewer } + standard_hash + gate + receipt_jws
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

  // Full composition_ref field set, per Liuyanfeng's confirmation. Optional
  // fields not used in this fixture are omitted entirely (consistent with
  // JCS + Liuyanfeng's resolution of open item #2).
  const compositionRefObject = {
    action_ref: `ao_action_${kind}_v03_demo_01`,
    delegation_ref: 'ao_delegation_v03_demo_01',
    revocation_ref: 'ao_revocation_v03_demo_01',
    key_source: 'inline',
    authority_verified_at_ms: AUTH_TS_MS,
    revocation_check_at_ms: REVOKE_TS_MS,
    scope: ACTION_SCOPE,
    version: COMPOSITION_REF_VERSION,
    metadata: {
      domain_verdicts: [domainVerdict],
    },
    composition_built_at_ms: BUILD_TS_MS,
  };

  const composition_ref = compositionRefHash(compositionRefObject);

  return {
    spec: 'argentum-core composition-ref-v1.0 (JCS canonical JSON, RFC 8785) per @Liuyanfeng1234 clarification in microsoft/autogen#7353',
    fields: compositionRefObject,
    computed: {
      composition_ref,
      hash_algorithm: 'SHA-256 over JCS canonical JSON (RFC 8785), first 16 hex chars',
      jcs_implementation: 'canonicalize@npm (RFC 8785 reference implementation)',
      jcs_canonical_bytes_length: jcs(compositionRefObject).length,
    },
    cross_references: {
      ietf_draft: 'https://datatracker.ietf.org/doc/draft-krausz-verification-state/',
      ao_receipt_spec: 'https://github.com/TKCollective/agentoracle-receipt-spec/tree/v0.3-binary-halt',
      argentum_core_field_def: 'https://github.com/giskard09/argentum-core/issues/10',
      aar_thread: 'https://github.com/microsoft/autogen/issues/7353',
    },
    notes: {
      version_value: `Used "${COMPOSITION_REF_VERSION}" — if CompositionRefBuilder expects a different canonical value for this field, flag and we converge.`,
      scope_value: `Used "${ACTION_SCOPE}" — per-action intent string per giskard09's definition. If a different canonical form is expected (e.g. a URN), flag and we converge.`,
      build_ts_field_name: `Used "composition_built_at_ms" for the composition-time timestamp (the "ts" element from the legacy pipe format). If CompositionRefBuilder names this field differently in the JCS object, flag and we converge.`,
    },
  };
}

const allowOut = buildOne({ kind: 'allow', jws: allowJws, payload: allowPayload });
const haltOut = buildOne({ kind: 'halt', jws: haltJws, payload: haltPayload });

writeFileSync(join(OUT, 'composition-ref-allow.json'), JSON.stringify(allowOut, null, 2) + '\n');
writeFileSync(join(OUT, 'composition-ref-halt.json'), JSON.stringify(haltOut, null, 2) + '\n');

console.log('AAR fixtures written (JCS mode):');
console.log('  composition-ref-allow.json  composition_ref =', allowOut.computed.composition_ref, ' (v_gate=' + allowPayload.v_gate + ')');
console.log('  composition-ref-halt.json   composition_ref =', haltOut.computed.composition_ref, ' (v_gate=' + haltPayload.v_gate + ')');
console.log('');
console.log('Hash algorithm: SHA-256 over JCS canonical JSON (RFC 8785), first 16 hex chars');
console.log('JCS implementation: canonicalize@npm (reference)');
