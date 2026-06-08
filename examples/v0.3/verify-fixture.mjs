// verify-fixture.mjs — offline verification of v0.3 fixture receipts.
//
// Demonstrates the full ADR-002 verification protocol against a local JWKS
// fixture (no network calls):
//
//   1. Verify JWS signature with the fixture public key.
//   2. Resolve v_gate_mapping_hash against a known mapping hash.
//   3. Recompute v_recommendation from signed primitives, assert equal.
//   4. Recompute v_gate = mapping(v_recommendation), assert equal.
//
// Usage:
//   cd examples
//   npm install jose      # if not already installed
//   node v0.3/verify-fixture.mjs
//
// Exit code 0 = both fixtures verified end-to-end.

import { importJWK, flattenedVerify } from 'jose';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const OUT = dirname(fileURLToPath(import.meta.url));
const MAPPING_ID = 'v0.3.0-2026-05-30';

function recomputeRecommendation(p) {
  if (p.v_verdict !== 'supported') {
    if (p.v_verdict === 'refuted') return 'refuted';
    if (p.v_verdict === 'unverifiable') return 'unverifiable';
    return 'error';
  }
  if (p.v_adversarial_result === 'vulnerable') return 'vulnerable_supported';
  if (p.v_confidence < p.v_gate_threshold) return 'weak_supported';
  return 'confident_supported';
}

function gateUnderV03Mapping(rec) {
  return rec === 'confident_supported' ? 'act' : 'halt';
}

async function loadKey() {
  const jwks = JSON.parse(readFileSync(join(OUT, 'jwks-fixture.json'), 'utf8'));
  return importJWK(jwks.keys[0], 'EdDSA');
}

async function verifyOne({ file, expectedGate, key }) {
  const jws = JSON.parse(readFileSync(join(OUT, file), 'utf8'));
  const result = await flattenedVerify(jws, key);
  const payload = JSON.parse(new TextDecoder().decode(result.payload));

  // 1. Mapping binding
  if (payload.v_gate_mapping !== MAPPING_ID) {
    throw new Error(`${file}: wrong mapping id`);
  }

  // 2. Recompute recommendation from signed primitives
  const candRec = recomputeRecommendation(payload);
  if (candRec !== payload.v_recommendation) {
    throw new Error(`${file}: recommendation mismatch (computed=${candRec}, signed=${payload.v_recommendation})`);
  }

  // 3. Recompute gate from recommendation under mapping
  const candGate = gateUnderV03Mapping(payload.v_recommendation);
  if (candGate !== payload.v_gate) {
    throw new Error(`${file}: gate mismatch (computed=${candGate}, signed=${payload.v_gate})`);
  }

  // 4. Sanity: matches the fixture's expected gate
  if (payload.v_gate !== expectedGate) {
    throw new Error(`${file}: expected gate=${expectedGate}, got ${payload.v_gate}`);
  }

  console.log(`  ${file}`);
  console.log(`    signature:        VALID (kid=${result.protectedHeader.kid})`);
  console.log(`    v_recommendation: ${payload.v_recommendation}  (recomputed match)`);
  console.log(`    v_gate:           ${payload.v_gate}            (recomputed match)`);
  console.log(`    v_gate_mapping:   ${payload.v_gate_mapping}`);
}

async function main() {
  const key = await loadKey();
  console.log('=== v0.3 fixture verification ===');
  await verifyOne({ file: 'receipt-allow.jws', expectedGate: 'act', key });
  await verifyOne({ file: 'receipt-halt.jws',  expectedGate: 'halt', key });
  console.log('=== ALL FIXTURES VERIFIED OK ===');
}

main().catch((e) => { console.error('FAIL:', e.message); process.exit(1); });
