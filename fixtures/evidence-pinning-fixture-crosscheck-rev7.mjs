#!/usr/bin/env node
// evidence-pinning fixture generator -- Node cross-check
//
// Spec bases (both re-derived from TKCollective/agentoracle-receipt-spec):
//   drafts/evidence-pinning-02-review-draft.md
//     sha256 9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096
//   drafts/evidence-pinning-02-amendments-rev5-2026-09-06.md
//     sha256 1f901fd7d56fcfe9f858446e5b685b540b5904d6abcfb4b2509e1eb675aa1e51
//
// THIS FILE IS NOT AN INDEPENDENT IMPLEMENTATION.
// It is authored by the same party as evidence-pinning-fixture-generator.py. Its purpose is
// to catch language-specific defects: JSON key ordering, UTF-8 handling,
// hashing library differences, integer widths, string comparison rules.
// If it agrees with the Python reference, that agreement is a cross-language
// check and MUST NOT be described as independent implementation. Independence
// for this section means a build from the specification text alone by a party
// with no access to these files.
//
// Usage:
//   node evidence-pinning-fixture-crosscheck.mjs               # emits evidence-pinning-fixtures-v2-rev5.json to stdout
//   node evidence-pinning-fixture-crosscheck.mjs --check evidence-pinning-fixtures-v2-rev5.json  # compares against a reference file

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import process from "node:process";

const LEAF_PREFIX = Buffer.from("ao-evidence-leaf-v2", "utf-8");
const NODE_PREFIX = Buffer.from("ao-evidence-node-v1", "utf-8");
// rev 6 Finding 27: node children are the 32 RAW OCTETS of the child digests.
// interiorHex below is the non-normative counter-construction (children as 64
// hex chars) and exists so this checker can verify evi-node-raw-not-hex's
// second value rather than skip it. A checker that skipped it would leave the
// one thing rev 6 adds uncovered.
const SEP = Buffer.from([0x00]);

const utf8 = (s) => Buffer.from(s, "utf-8");
const sha256 = (buf) => createHash("sha256").update(buf).digest();
const sha256hex = (s) => createHash("sha256").update(utf8(s)).digest("hex");

// distinctness on the four bound members (rev 5 Finding 24)
function checkDistinct(entries) {
  const seen = new Set();
  for (const e of entries) {
    const key = JSON.stringify([e.url, e.snippet_sha256, e.content_kind, e.retrieved_at]);
    if (seen.has(key)) throw new Error(`duplicate bound tuple: ${key}`);
    seen.add(key);
  }
}

// four-term sort, bytewise UTF-8 (rev 4 15c amended by rev 5 24c)
function sortKey(e) {
  return [utf8(e.url), utf8(e.snippet_sha256), utf8(e.content_kind), utf8(e.retrieved_at)];
}
function cmpBuf(a, b) { return Buffer.compare(a, b); }
function cmpKey(a, b) {
  for (let i = 0; i < a.length; i++) { const c = cmpBuf(a[i], b[i]); if (c !== 0) return c; }
  return 0;
}

// leaf preimage: LEAF_PREFIX || 0x00 || url || 0x00 || snippet_sha256 || 0x00 || content_kind || 0x00 || retrieved_at
function leaf(e) {
  return sha256(Buffer.concat([LEAF_PREFIX, SEP,
                               utf8(e.url), SEP,
                               utf8(e.snippet_sha256), SEP,
                               utf8(e.content_kind), SEP,
                               utf8(e.retrieved_at)]));
}
function interior(l, r) {
  return sha256(Buffer.concat([NODE_PREFIX, SEP, l, SEP, r]));
}
// NON-NORMATIVE. Leaf preimage with snippet_sha256 as its 32 raw octets rather
// than its 64 hex characters. Exists so non_normative_raw_root is checked rather
// than skipped: the rev 5 checker skipped it, leaving one asserted value in the
// file that no implementation verified.
function leafRawDigest(e) {
  return sha256(Buffer.concat([LEAF_PREFIX, SEP,
                               utf8(e.url), SEP,
                               Buffer.from(e.snippet_sha256, "hex"), SEP,
                               utf8(e.content_kind), SEP,
                               utf8(e.retrieved_at)]));
}
// NON-NORMATIVE. Children as their 64 lowercase hex characters, UTF-8.
function interiorHex(l, r) {
  return sha256(Buffer.concat([NODE_PREFIX, SEP,
                               utf8(l.toString("hex")), SEP,
                               utf8(r.toString("hex"))]));
}
function rootWith(entries, nodeFn) {
  const pinned = entries.filter(e => e.pinned !== false);
  if (pinned.length === 0) return null;
  const sorted = pinned.map(e => ({ e, k: sortKey(e) }))
                       .sort((a, b) => cmpKey(a.k, b.k))
                       .map(x => x.e);
  let level = sorted.map(leaf);
  while (level.length > 1) {
    const next = [];
    let i = 0;
    while (i + 1 < level.length) { next.push(nodeFn(level[i], level[i+1])); i += 2; }
    if (i < level.length) next.push(level[i]);  // odd: promote unchanged
    level = next;
  }
  return level[0].toString("hex");
}
function root(entries) { return rootWith(entries, interior); }
function rootHexChildren(entries) { return rootWith(entries, interiorHex); }
function evidenceRoot(entries) { checkDistinct(entries); return root(entries); }
function evidenceRootHexChildren(entries) { checkDistinct(entries); return rootHexChildren(entries); }

// -------- if invoked with --check, verify against a reference fixture --------
// Recomputes every root in the file using this Node implementation and diffs.
// This is the cross-language check itself; the reference file is passed in.
// rev 7: the Finding 34 de-disclosure renamed the encoding vectors' computed keys
// to `normative_root` / `counter_construction_root`, which are deliberately NOT
// self-describing. Both encoding vectors now use the same two key names with
// DIFFERENT constructions, so dispatch is on (vector id, key) rather than key
// alone. That is the intended cost: the checker is the authoring party and is
// allowed to know which construction applies; a fixture consumer is not.
// An unrecognised root key is a FAILURE, not a skip.
if (process.argv[2] === "--check") {
  const ref = JSON.parse(readFileSync(process.argv[3], "utf-8"));
  const fails = [];

  // rev 7 Finding 33: every MALFORMED vector names exactly one condition, and
  // no two vectors claim the same one. Checked here as well as in the generator
  // so the shipped artifact is verified, not just the emitter.
  {
    const missing = ref.vectors.filter(v => v.designation === "MALFORMED" && !v.condition).map(v => v.id);
    for (const id of missing) fails.push(`${id}: MALFORMED without a condition member (rev 7 Finding 33)`);
    const conds = ref.vectors.filter(v => v.condition).map(v => v.condition);
    for (const c of new Set(conds)) {
      if (conds.filter(x => x === c).length > 1) fails.push(`duplicate condition identifier: ${c}`);
    }
  }

  // rev 7 Finding 34: no identifier or computed key names the resolution it tests.
  {
    const TOK = ["raw", "hex", "not-hex", "not_hex", "octet", "normative_raw", "normative_hex", "non_normative"];
    for (const v of ref.vectors) {
      for (const t of TOK) {
        if (v.id.toLowerCase().includes(t)) fails.push(`${v.id}: id contains resolution token "${t}" (rev 7 Finding 34)`);
      }
      for (const k of Object.keys(v.computed || {})) {
        for (const t of TOK) {
          if (k.toLowerCase().includes(t)) fails.push(`${v.id}: computed key "${k}" contains resolution token "${t}" (rev 7 Finding 34)`);
        }
      }
    }
  }
  const recomputed = [];
  for (const v of ref.vectors) {
    const c = v.computed;
    if (!c) continue;
    for (const [k, expected] of Object.entries(c)) {
      // Explicit allowlist of every root-valued key in the rev 6 set, each with
      // the input it is computed from and which construction computes it.
      // A key absent from this table is REPORTED, not silently skipped: an
      // unrecognised root key means the checker does not cover a value the
      // fixture asserts, and the run must say so rather than pass quietly.
      const RAW = "raw", HEX = "hex";
      let entries = null, mode = RAW;
      if (k === "root") {
        entries = Array.isArray(v.input) ? v.input : (v.input.entry ? [v.input.entry] : null);
      } else if (k === "root_1") { entries = v.input.set_1; }
      else if (k === "root_2") { entries = v.input.set_2; }
      else if (k === "correct_root") { entries = v.input.evidence_set.sources; }
      // rev 7 Finding 33a vector.
      else if (k === "evidence_root") { entries = v.input.evidence_set.sources; }
      // rev 7 Finding 34: same key names on two vectors, different constructions.
      else if (k === "normative_root" || k === "counter_construction_root") {
        if (v.id === "evi-leaf-member-encoding") {
          entries = [v.input.entry];
          mode = (k === "counter_construction_root") ? "leafraw" : RAW;
        } else if (v.id === "evi-node-child-encoding") {
          entries = v.input.sources;
          mode = (k === "counter_construction_root") ? HEX : RAW;
        } else {
          fails.push(`${v.id}.${k}: de-disclosed root key on a vector the checker has no rule for`);
          continue;
        }
      }
      else if (k === "differ") { continue; }  // boolean, not a root
      else if (/root/i.test(k)) {
        fails.push(`${v.id}.${k}: UNCOVERED root key — checker has no rule for it`);
        continue;
      } else { continue; }  // not a root-valued key at all

      if (!entries) {
        fails.push(`${v.id}.${k}: no input entries resolved for a root key`);
        continue;
      }
      let got;
      try {
        if (mode === "leafraw") {
          // single pinned entry: the root is the leaf, under the raw-digest form
          if (entries.length !== 1) throw new Error("leafraw expects one entry");
          got = leafRawDigest(entries[0]).toString("hex");
        } else if (mode === HEX) { got = evidenceRootHexChildren(entries); }
        else { got = evidenceRoot(entries); }
      }
      catch (e) { fails.push(`${v.id}.${k}: ${e.message}`); continue; }
      recomputed.push({ id: v.id, key: k, mode, expected, got, match: got === expected });
      if (got !== expected) fails.push(`${v.id}.${k}: expected ${expected}, got ${got}`);
    }
  }
  const report = {
    reference_file: process.argv[3],
    reference_json_sha256: createHash("sha256").update(readFileSync(process.argv[3])).digest("hex"),
    total_roots_checked: recomputed.length,
    roots_checked_raw_children: recomputed.filter(r => r.mode === "raw").length,
    roots_checked_hex_children: recomputed.filter(r => r.mode === "hex").length,
    roots_checked_leaf_raw_digest: recomputed.filter(r => r.mode === "leafraw").length,
    vectors_in_file: ref.vectors.length,
    mismatches: fails.length,
    all_agree: fails.length === 0,
    failures: fails,
  };
  console.log(JSON.stringify(report, null, 2));
  process.exit(fails.length === 0 ? 0 : 1);
}

// -------- emit evidence-pinning-fixtures-v2-rev5.json in the same shape as the Python reference --------
// (This path exists so the two files can be diff'd directly; the primary use
//  is --check against the Python-emitted evidence-pinning-fixtures-v2-rev5.json.)
console.error("Use --check <evidence-pinning-fixtures-v2-rev6.json> to run the cross-language check.");
console.error("Direct emission is not implemented in the Node file; the Python");
console.error("reference is the sole emitter, per the disclosure at the top of");
console.error("each file. This preserves one emitter and one checker.");
process.exit(2);
