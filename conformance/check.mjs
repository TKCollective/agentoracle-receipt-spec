#!/usr/bin/env node
// Rule-6 conformance runner. Drafted 2026-08-27. NOT wired into CI yet.
//
// Asserts the v0.3 recommendation_rules + gate_map derivation against
// tracker/conformance_vectors_rule2.json. Exits non-zero on any failure so it
// can become a build gate (standing_rules/service_integrity.md rule 6).
//
// The derivation under test is a transcription of v_gate_compose.js:950-975.
// It is deliberately a SEPARATE implementation: if the runner imported the
// function it tests, a regression in that function would silently update the
// expectation. A second implementation is the point.
//
// Usage:
//   node conformance_check.mjs tracker/conformance_vectors_rule2.json
//   node conformance_check.mjs vectors.json --verbose

import { readFileSync } from "node:fs";

const V_GATE_THRESHOLD = 0.7;

function derive(v_verdict, v_adversarial_result, v_confidence) {
  let v_recommendation;
  if (v_verdict === "refuted") {
    v_recommendation = "refuted";                                   // rule 5
  } else if (v_verdict === "unverifiable" || v_verdict === "unknown") {
    v_recommendation = "unverifiable";                              // rule 6
  } else {
    if (v_adversarial_result === "resilient" && v_confidence >= V_GATE_THRESHOLD) {
      v_recommendation = "confident_supported";                     // rule 1
    } else if (v_adversarial_result === "not_checked" && v_confidence >= V_GATE_THRESHOLD) {
      v_recommendation = "un_probed_not_cleared";                   // rule 2
    } else if (v_adversarial_result === "vulnerable") {
      v_recommendation = "vulnerable_supported";                    // rule 3
    } else if (
      (v_adversarial_result === "resilient" || v_adversarial_result === "not_checked") &&
      v_confidence < V_GATE_THRESHOLD
    ) {
      v_recommendation = "weak_supported";                          // rule 4
    } else {
      v_recommendation = "error";                                   // rule 7
    }
  }
  const verdict = v_recommendation === "confident_supported" ? "act" : "halt";
  return { v_recommendation, verdict };
}

const path = process.argv[2] || new URL("./vectors-rule2.json", import.meta.url);
const verbose = process.argv.includes("--verbose");
const doc = JSON.parse(readFileSync(path, "utf-8"));

if (doc.v_gate_threshold !== V_GATE_THRESHOLD) {
  console.error(
    `FAIL threshold: vectors declare ${doc.v_gate_threshold}, runner uses ${V_GATE_THRESHOLD}. ` +
    `The mapping threshold is not caller-tunable; one of these is wrong.`
  );
  process.exit(1);
}

let pass = 0, fail = 0, skip = 0;
const failures = [];

for (const v of doc.vectors) {
  // D1 is an absence assertion about the service, not a derivation. The rule
  // table cannot express "no receipt was issued", so it is not run here.
  if (v.input && Object.prototype.hasOwnProperty.call(v.input, "members_evaluated")) {
    skip++;
    if (verbose) console.log(`  SKIP  ${v.id}  (service-level, not a gate derivation)`);
    continue;
  }

  const got = derive(v.input.v_verdict, v.input.v_adversarial_result, v.input.v_confidence);
  const problems = [];

  if (v.expect) {
    for (const [k, want] of Object.entries(v.expect)) {
      if (got[k] !== want) problems.push(`${k}: expected ${JSON.stringify(want)}, got ${JSON.stringify(got[k])}`);
    }
  }
  if (v.expect_must_not_equal) {
    for (const [k, forbidden] of Object.entries(v.expect_must_not_equal)) {
      if (got[k] === forbidden) problems.push(`${k}: MUST NOT be ${JSON.stringify(forbidden)}, but is`);
    }
  }
  if (!v.expect && !v.expect_must_not_equal) {
    problems.push("vector declares neither expect nor expect_must_not_equal");
  }

  if (problems.length === 0) {
    pass++;
    if (verbose) {
      console.log(`  PASS  ${v.id.padEnd(24)} -> ${got.v_recommendation} / ${got.verdict}`);
    }
  } else {
    fail++;
    failures.push({ id: v.id, designation: v.designation, problems, got });
  }
}

console.log(`\nvectors: ${pass} passed, ${fail} failed, ${skip} skipped (service-level)`);

if (fail > 0) {
  console.error("\nFAILURES:");
  for (const f of failures) {
    console.error(`\n  ${f.id}  [${f.designation}]`);
    for (const p of f.problems) console.error(`    - ${p}`);
    console.error(`    derived: ${JSON.stringify(f.got)}`);
  }
  console.error(
    "\nA failure here means the recommendation table or gate_map changed. " +
    "If the change was intentional, the mapping version and its hash must change too — " +
    "v0.3 receipts already in circulation were derived under the old table."
  );
  process.exit(1);
}

console.log("rule table conforms to mapping-agentoracle-v0.3-2026-05-30");
console.log(`NOTE: ${skip} service-level vector(s) not covered here — D1 needs a request-level test.`);
