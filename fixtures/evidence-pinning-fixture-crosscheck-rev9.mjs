#!/usr/bin/env node
// evidence-pinning fixture generator rev 9 -- Node cross-check
//
// NEW FILENAME per semantics_change_new_filename.md. Everything the rev 8
// cross-check did is kept (roots, census, Findings 35-37 scope discrimination,
// superseded identifiers). Rev 9 adds:
//   Finding 47  in every vector that is not MALFORMED, every unpinned entry
//               carries snippet_sha256, and it is null;
//   Finding 48  the member-absent vector exists, names snippet_sha256_member_absent,
//               and its entry really omits the member;
//   Finding 49  the eight pre-registry condition identifiers are superseded and
//               published as such; a vector naming one fails;
//   Finding 50  the two contributed vectors (babyblueviper1, CC0) are present with
//               their attribution, the mixed pair discriminates the two readings of
//               the identity rule, and the roots they carry recompute.
//
// Spec bases (both re-derived from TKCollective/agentoracle-receipt-spec):
//   drafts/evidence-pinning-02-review-draft.md
//     sha256 9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096
//   drafts/evidence-pinning-02-amendments-rev5-2026-09-06.md
//     sha256 1f901fd7d56fcfe9f858446e5b685b540b5904d6abcfb4b2509e1eb675aa1e51
//
// THIS FILE IS NOT AN INDEPENDENT IMPLEMENTATION.
// It is authored by the same party as evidence-pinning-fixture-generator-rev9.py. Its purpose is
// to catch language-specific defects: JSON key ordering, UTF-8 handling,
// hashing library differences, integer widths, string comparison rules.
// If it agrees with the Python reference, that agreement is a cross-language
// check and MUST NOT be described as independent implementation. Independence
// for this section means a build from the specification text alone by a party
// with no access to these files.
//
// Usage:
//   node evidence-pinning-fixture-crosscheck-rev9.mjs --check evidence-pinning-fixtures-v2-rev9.json  # checks a reference file

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

const isPinned = (e) => e.pinned !== false;

// rev 8 Finding 35: the entry-identity rule ranges over EVERY entry in `sources`.
// Identical url and retrieved_at is one retrieval; snippet_sha256 and content_kind
// discriminate only when both entries are pinned. Absent and null are the same
// here, which is why the members are read with ?? null rather than by presence.
function checkDistinct(entries) {
  const buckets = new Map();
  for (const e of entries) {
    const k = JSON.stringify([e.url, e.retrieved_at]);
    if (!buckets.has(k)) buckets.set(k, []);
    buckets.get(k).push(e);
  }
  for (const [k, group] of buckets) {
    for (let i = 0; i < group.length; i++) {
      for (let j = i + 1; j < group.length; j++) {
        const a = group[i], b = group[j];
        if (isPinned(a) && isPinned(b)) {
          if ((a.snippet_sha256 ?? null) === (b.snippet_sha256 ?? null) &&
              (a.content_kind ?? null) === (b.content_kind ?? null)) {
            throw new Error(`duplicate bound tuple: ${k}`);
          }
        } else {
          throw new Error(`duplicate bound tuple: ${k}`);
        }
      }
    }
  }
}

// NON-NORMATIVE under rev 8: the pinned-only reading, kept only so this file can
// prove the rev 8 vectors discriminate between the two readings.
function checkDistinctPinnedOnly(entries) {
  const seen = new Set();
  for (const e of entries) {
    if (!isPinned(e)) continue;
    const key = JSON.stringify([e.url, e.snippet_sha256 ?? null, e.content_kind ?? null, e.retrieved_at]);
    if (seen.has(key)) throw new Error(`duplicate bound tuple: ${key}`);
    seen.add(key);
  }
}

// rev 8 Finding 36: bytewise-least retrieved_at over all entries, UTF-8 as carried.
function leastRetrievedAt(entries, pinnedOnly = false) {
  const vals = entries.filter(e => !pinnedOnly || isPinned(e)).map(e => utf8(e.retrieved_at));
  if (vals.length === 0) return null;
  return vals.reduce((a, b) => (Buffer.compare(a, b) <= 0 ? a : b)).toString("utf-8");
}

// rev 8 Finding 37: the form rule ranges over every entry, before any branch on pinned.
const CANONICAL_RETRIEVED_AT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/;
function firstNoncanonical(entries, pinnedOnly = false) {
  for (const e of entries) {
    if (pinnedOnly && !isPinned(e)) continue;
    if (typeof e.retrieved_at !== "string" || !CANONICAL_RETRIEVED_AT.test(e.retrieved_at)) return e;
  }
  return null;
}

const SUPERSEDED_CONDITIONS = {
  // superseded at rev 8 (Finding 38)
  pinned_set_empty: "evidence_set_names_no_sources",
  set_retrieved_at_not_first_in_canonical_order: "set_retrieved_at_not_bytewise_least",
  // superseded at rev 9 (Finding 49): the -03 registry names
  content_kind_absent_when_pinned: "content_kind_absent_or_invalid_when_pinned",
  pinned_count_disagrees_with_pinned_entries: "pinned_count_mismatch",
  root_null_with_pinned_entries: "evidence_root_absent_with_pinned_items",
  root_present_with_zero_pinned: "evidence_root_present_with_no_pinned_items",
  snippet_digest_present_for_full_resource: "resource_sha256_present_for_full_resource",
  source_count_disagrees_with_sources: "source_count_mismatch",
  unpinned_reason_outside_domain: "unpinned_reason_absent_or_invalid",
  unpinned_without_reason: "unpinned_reason_absent_or_invalid",
};

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

  // rev 7 Finding 33, as amended by rev 8 Finding 39: every MALFORMED vector
  // names exactly one condition. The uniqueness assertion is GONE -- rev 8
  // injects three already-vectored conditions on a different entry class, and
  // uniqueness would fail a correct set. What replaces it: no vector may name an
  // identifier this revision superseded (rev 8 Finding 38).
  {
    const missing = ref.vectors.filter(v => v.designation === "MALFORMED" && !v.condition).map(v => v.id);
    for (const id of missing) fails.push(`${id}: MALFORMED without a condition member (rev 7 Finding 33)`);
    for (const v of ref.vectors) {
      if (v.condition && Object.hasOwn(SUPERSEDED_CONDITIONS, v.condition)) {
        fails.push(`${v.id}: names superseded condition "${v.condition}" (rev 8 Finding 38 / rev 9 Finding 49); ` +
                   `rev 9 requires "${SUPERSEDED_CONDITIONS[v.condition]}"`);
      }
    }
    const declared = ref.header?.superseded_conditions ?? {};
    for (const [old, now] of Object.entries(SUPERSEDED_CONDITIONS)) {
      if (declared[old] !== now) {
        fails.push(`header.superseded_conditions does not publish ${old} -> ${now} (rev 8 Finding 38 / rev 9 Finding 49)`);
      }
    }
  }

  // rev 8: the four new vectors must DISCRIMINATE. Each is evaluated under both
  // the whole-of-`sources` reading and the pinned-only reading, and it is a
  // FAILURE if the two agree -- a vector that cannot fail on the defect it was
  // added for is not evidence. This is the check the rev 7 set lacked, and it is
  // run here against the shipped file rather than only inside the emitter.
  {
    const byId = new Map(ref.vectors.map(v => [v.id, v]));
    const srcOf = (id) => byId.get(id)?.input?.evidence_set?.sources;
    const raises = (fn, arg) => { try { fn(arg); return false; } catch { return true; } };

    const dup = srcOf("evi-duplicate-unpinned-entries-rejects");
    if (!dup) fails.push("evi-duplicate-unpinned-entries-rejects: missing from the set (rev 8 Finding 35)");
    else {
      if (!raises(checkDistinct, dup)) fails.push("evi-duplicate-unpinned-entries-rejects: rev 8 identity rule does not halt");
      if (raises(checkDistinctPinnedOnly, dup)) fails.push("evi-duplicate-unpinned-entries-rejects: pinned-only reading also halts; vector does not discriminate");
    }

    const nc = srcOf("evi-unpinned-retrieved-at-noncanonical-rejects");
    if (!nc) fails.push("evi-unpinned-retrieved-at-noncanonical-rejects: missing from the set (rev 8 Finding 37)");
    else {
      if (firstNoncanonical(nc) === null) fails.push("evi-unpinned-retrieved-at-noncanonical-rejects: no non-canonical value present");
      if (firstNoncanonical(nc, true) !== null) fails.push("evi-unpinned-retrieved-at-noncanonical-rejects: a pinned entry also carries one; vector does not discriminate");
    }

    for (const [id, wantAll] of [["evi-set-retrieved-at-equals-unpinned-value", true],
                                 ["evi-set-retrieved-at-above-unpinned-value-rejects", false]]) {
      const es = byId.get(id)?.input?.evidence_set;
      if (!es) { fails.push(`${id}: missing from the set (rev 8 Finding 36)`); continue; }
      const all = leastRetrievedAt(es.sources);
      const pinnedOnly = leastRetrievedAt(es.sources, true);
      if (all === pinnedOnly) fails.push(`${id}: both domains give the same value; vector does not discriminate`);
      if ((es.retrieved_at === all) !== wantAll) fails.push(`${id}: set-level retrieved_at is not where the vector requires it`);
      if ((es.retrieved_at === pinnedOnly) === wantAll) fails.push(`${id}: set-level retrieved_at is not where the vector requires it under the pinned-only reading`);
    }
  }

  // rev 9 Findings 47, 48, 50.
  {
    const byId = new Map(ref.vectors.map(v => [v.id, v]));
    const raises = (fn, arg) => { try { fn(arg); return false; } catch { return true; } };
    const entriesIn = (v) => { const out = []; const walk = (n) => { if (Array.isArray(n)) n.forEach(walk); else if (n && typeof n === "object") { if ("url" in n && "retrieved_at" in n) out.push(n); Object.values(n).forEach(walk); } }; walk(v.input); return out; };
    // Finding 47: no non-MALFORMED vector carries an unpinned entry without an explicit null snippet_sha256.
    for (const v of ref.vectors) {
      if (v.designation === "MALFORMED") continue;
      for (const e of entriesIn(v)) {
        if (e.pinned === false && (!Object.hasOwn(e, "snippet_sha256") || e.snippet_sha256 !== null)) {
          fails.push(`${v.id}: unpinned entry without an explicit null snippet_sha256 (rev 9 Finding 47)`);
        }
      }
    }
    for (const id of ["evi-fully-pinned-fallback-derives-from-sources-accepted", "evi-root-present-pinned-count-absent-accepted",
                      "evi-unpinned-item-reason-content-not-held", "evi-unpinned-members-absent-accepted"]) {
      if (!byId.has(id)) fails.push(`${id}: one of the four regenerated fixtures is missing (rev 9 Finding 47)`);
    }
    // Finding 48: the negative vector.
    const neg = byId.get("evi-snippet-sha256-member-absent-on-unpinned-rejects");
    if (!neg) fails.push("evi-snippet-sha256-member-absent-on-unpinned-rejects: missing from the set (rev 9 Finding 48)");
    else {
      if (neg.designation !== "MALFORMED" || neg.condition !== "snippet_sha256_member_absent") fails.push("member-absent vector: wrong designation or condition");
      const e = neg.input?.entry;
      if (!e || Object.hasOwn(e, "snippet_sha256")) fails.push("member-absent vector: its entry carries the member it exists to omit");
      else if (e.pinned !== false || !e.unpinned_reason || !CANONICAL_RETRIEVED_AT.test(e.retrieved_at)) fails.push("member-absent vector: its entry breaks a second rule");
    }
    // Finding 50: the contributed pair.
    const rej = byId.get("evi-duplicate-pinned-unpinned-pair-rejects");
    const acc = byId.get("evi-pinned-unpinned-same-url-distinct-time-accepted");
    for (const [id, v] of [["evi-duplicate-pinned-unpinned-pair-rejects", rej], ["evi-pinned-unpinned-same-url-distinct-time-accepted", acc]]) {
      if (!v) { fails.push(`${id}: missing from the set (rev 9 Finding 50)`); continue; }
      if (v.contributed_by !== "babyblueviper1" || v.license !== "CC0-1.0" || !v.source) fails.push(`${id}: attribution members missing or changed`);
      const es = v.input?.evidence_set;
      if (!es) { fails.push(`${id}: no evidence_set`); continue; }
      const got = root(es.sources);
      if (got !== es.evidence_root) fails.push(`${id}: carried evidence_root ${es.evidence_root} is not the root of its pinned entries (${got})`);
    }
    if (rej) {
      const src = rej.input.evidence_set.sources;
      if (rej.condition !== "duplicate_bound_tuple") fails.push("mixed pair: condition is not duplicate_bound_tuple");
      if (!raises(checkDistinct, src)) fails.push("mixed pair: identity rule does not halt");
      if (raises(checkDistinctPinnedOnly, src)) fails.push("mixed pair: pinned-only reading also halts; vector does not discriminate");
    }
    if (acc && raises(checkDistinct, acc.input.evidence_set.sources)) fails.push("distinct-time pair: identity rule halts on two retrievals");
    const cvh = ref.header?.contributed_vectors;
    if (!cvh || cvh.author !== "babyblueviper1" || cvh.license !== "CC0-1.0" || (cvh.ids || []).length !== 2) fails.push("header.contributed_vectors does not record the two CC0 vectors and their author");
  }

  // rev 8: re-derive every count in header.census from the shipped vectors.
  // rev 7's E-4 was a hand-written group count that disagreed with the set; a
  // census that is not recomputed is the same defect waiting to recur.
  {
    const c = ref.header?.census;
    if (!c) fails.push("header.census absent (rev 8)");
    else {
      const entriesOf = (v) => {
        const out = [];
        const walk = (n) => {
          if (Array.isArray(n)) n.forEach(walk);
          else if (n && typeof n === "object") {
            if ("url" in n && "retrieved_at" in n) out.push(n);
            Object.values(n).forEach(walk);
          }
        };
        walk(v.input);
        return out;
      };
      const rootBearing = ref.vectors.filter(v => v.computed && Object.keys(v.computed).length);
      const malformed = ref.vectors.filter(v => v.designation === "MALFORMED");
      const overlap = rootBearing.filter(v => malformed.includes(v));
      const remaining = ref.vectors.filter(v => !rootBearing.includes(v) && !malformed.includes(v));
      const rootValues = ref.vectors.reduce((n, v) =>
        n + Object.keys(v.computed || {}).filter(k => k.toLowerCase().includes("root")).length, 0);
      const allEntries = ref.vectors.flatMap(entriesOf);
      const unpinned = allEntries.filter(e => e.pinned === false);
      const derived = {
        total: ref.vectors.length,
        root_bearing: rootBearing.length,
        root_values: rootValues,
        malformed: malformed.length,
        remaining: remaining.length,
        overlap: overlap.length,
        entry_objects: allEntries.length,
        entries_pinned: allEntries.length - unpinned.length,
        entries_unpinned: unpinned.length,
        vectors_carrying_unpinned_entries: ref.vectors.filter(v => entriesOf(v).some(e => e.pinned === false)).length,
      };
      for (const [k, want] of Object.entries(derived)) {
        if (c[k] !== want) fails.push(`header.census.${k}: file says ${c[k]}, recomputed ${want}`);
      }
      if (rootBearing.length + malformed.length + remaining.length - overlap.length !== ref.vectors.length) {
        fails.push("group arithmetic does not reach the vector total (rev 7 E-4's class)");
      }
      if (ref.header.vector_count !== ref.vectors.length) {
        fails.push(`header.vector_count ${ref.header.vector_count} != ${ref.vectors.length} vectors`);
      }
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

// -------- no emitter: the Python reference is the sole emitter --------
console.error("Use --check <evidence-pinning-fixtures-v2-rev9.json> to run the cross-language check.");
console.error("Direct emission is not implemented in the Node file; the Python");
console.error("reference is the sole emitter, per the disclosure at the top of");
console.error("each file. This preserves one emitter and one checker.");
process.exit(2);
