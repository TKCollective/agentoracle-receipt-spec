// build-fixtures.mjs — one-shot generator for v0.3 fixture pair.
//
// Produces:
//   - jwks-fixture.json   (static Ed25519 public key, offline verifiable)
//   - canonical-input.json (shared canonical inputs both receipts derive from)
//   - receipt-allow.jws   (v_recommendation=confident_supported, v_gate=act)
//   - receipt-halt.jws    (v_recommendation=vulnerable_supported, v_gate=halt)
//
// Both receipts share the same v_verdict, claim, and surrounding context.
// They differ only in v_adversarial_result, which under mapping
// v0.3.0-2026-05-30 flips v_recommendation and therefore v_gate.

import { generateKeyPair, exportJWK, FlattenedSign } from 'jose';
import { createHash } from 'node:crypto';
import { writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const OUT = dirname(fileURLToPath(import.meta.url));

const ALG = 'EdDSA';
const KID = 'ao-fixture-2026-06-v03-ed25519';
const MAPPING_ID = 'v0.3.0-2026-05-30';
const MAPPING_HASH = sha256OfMappingDoc(); // computed below

// Deterministic content-addressed hash of the published mapping doc.
function sha256OfMappingDoc() {
  // For a real receipt this hashes the exact bytes of the published mapping
  // file. For the fixture we hash a stable identifier string so the fixture
  // is reproducible by anyone running this script.
  const stableMaterial = `agentoracle-receipt-spec://mappings/${MAPPING_ID}.md`;
  return 'sha256-' + createHash('sha256').update(stableMaterial).digest('hex');
}

function makeCanonicalInput() {
  return {
    receipt_version: '0.3.0',
    mapping_id: MAPPING_ID,
    issuer: 'https://agentoracle.co',
    subject: {
      type: 'verification.factual_claim',
      claim_text: 'The Eiffel Tower is located in Paris, France.',
      claim_hash: 'sha256-' + createHash('sha256')
        .update('The Eiffel Tower is located in Paris, France.')
        .digest('hex'),
    },
    context: {
      action_ref: 'urn:agentoracle:demo:claim-verify:0001',
      scope: 'general_factual_claims_en',
      issued_at_planned: '2026-06-08T00:00:00Z',
    },
  };
}

function makeReceiptPayload({ evalId, adversarialResult, issuedAt, canonical }) {
  // Signed primitives (per ADR-002 v0.3 receipt structure)
  const v_verdict = 'supported';
  const v_confidence = 0.91;
  const v_gate_threshold = 0.70;
  // v_recommendation is derived from v_verdict, v_confidence vs threshold,
  // and v_adversarial_result. The verifier MUST recompute and check.
  let v_recommendation;
  if (v_verdict !== 'supported') {
    v_recommendation = v_verdict === 'refuted' ? 'refuted' : 'unverifiable';
  } else if (adversarialResult === 'vulnerable') {
    v_recommendation = 'vulnerable_supported';
  } else if (v_confidence < v_gate_threshold) {
    v_recommendation = 'weak_supported';
  } else {
    v_recommendation = 'confident_supported';
  }
  // Gate function under mapping v0.3.0-2026-05-30
  const v_gate = v_recommendation === 'confident_supported' ? 'act' : 'halt';

  return {
    ...canonical,
    evaluation_id: evalId,
    issued_at: issuedAt,
    // Canonical signed primitives
    v_verdict,
    v_confidence,
    v_gate_threshold,
    v_adversarial_result: adversarialResult,
    v_sources_used: ['sonar', 'adversarial'],
    // Canonical recommendation (signed)
    v_recommendation,
    // Derived gate (signed)
    v_gate,
    // Mapping binding (signed)
    v_gate_mapping: MAPPING_ID,
    v_gate_mapping_hash: MAPPING_HASH,
    // Evidence (signed, not gating)
    evidence: {
      sources_consulted: 4,
      sources_concurring: 4,
      corpus_snapshot: '2026-Q2',
    },
    signature_meta: {
      jwks_url: 'https://agentoracle.co/.well-known/jwks.json',
      valid_until: '2026-09-08T00:00:00Z',
    },
  };
}

async function signReceipt({ payload, privateKey }) {
  const enc = new TextEncoder();
  const jws = await new FlattenedSign(enc.encode(JSON.stringify(payload)))
    .setProtectedHeader({
      alg: ALG,
      kid: KID,
      typ: 'application/vnd.agentoracle.receipt+jws',
      cty: 'application/json',
    })
    .sign(privateKey);
  return jws;
}

async function main() {
  const { publicKey, privateKey } = await generateKeyPair(ALG, { extractable: true });
  const jwk = await exportJWK(publicKey);
  jwk.kid = KID;
  jwk.alg = ALG;
  jwk.use = 'sig';

  const jwks = { keys: [jwk] };
  writeFileSync(join(OUT, 'jwks-fixture.json'), JSON.stringify(jwks, null, 2) + '\n');

  const canonical = makeCanonicalInput();
  writeFileSync(join(OUT, 'canonical-input.json'), JSON.stringify(canonical, null, 2) + '\n');

  const allowPayload = makeReceiptPayload({
    evalId: 'ao_eval_fixture_v03_allow_01',
    adversarialResult: 'resilient',
    issuedAt: '2026-06-08T00:00:00Z',
    canonical,
  });
  const haltPayload = makeReceiptPayload({
    evalId: 'ao_eval_fixture_v03_halt_01',
    adversarialResult: 'vulnerable',
    issuedAt: '2026-06-08T00:00:01Z',
    canonical,
  });

  // Sanity invariants before signing
  if (allowPayload.v_gate !== 'act') throw new Error('expected allow.v_gate = act');
  if (haltPayload.v_gate !== 'halt') throw new Error('expected halt.v_gate = halt');
  if (allowPayload.v_recommendation !== 'confident_supported') throw new Error('allow rec');
  if (haltPayload.v_recommendation !== 'vulnerable_supported') throw new Error('halt rec');

  const allowJws = await signReceipt({ payload: allowPayload, privateKey });
  const haltJws = await signReceipt({ payload: haltPayload, privateKey });

  writeFileSync(join(OUT, 'receipt-allow.jws'), JSON.stringify(allowJws, null, 2) + '\n');
  writeFileSync(join(OUT, 'receipt-halt.jws'), JSON.stringify(haltJws, null, 2) + '\n');

  console.log('Fixtures written:');
  console.log('  jwks-fixture.json');
  console.log('  canonical-input.json');
  console.log('  receipt-allow.jws  →  v_gate=act');
  console.log('  receipt-halt.jws   →  v_gate=halt');
  console.log('  mapping_id =', MAPPING_ID);
  console.log('  mapping_hash =', MAPPING_HASH);
}

main().catch((e) => { console.error(e); process.exit(1); });
