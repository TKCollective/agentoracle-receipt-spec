#!/usr/bin/env python3
"""Validate mapping.json against the corpus at its snapshot commit, the cited
texts and the schema. Independent of the generator. It checks that
  1. every corpus's manifest, read with `git show <corpus_snapshot.commit>:<path>`
     (never the working tree), has the recorded sha256 and the recorded count,
     and every mapped vector id exists in it (and vice versa);
  2. every requirement identifier referenced exists in the registry, and every
     registry identifier appears in the reverse view;
  3. every vector carries at least one in-scope requirement link, or an explicit
     status "deferred" with a reason (and a deferred vector carries no coverage);
  4. the reverse view EQUALS the forward view scoped to the corpora each view names
     (every hit and the best coverage), recomputed here; for views that publish a
     second count excluding not-normative corpora, that count is recomputed too;
  5. the digests recorded for the cited -01 text and the mapping document are
     recomputed from the cited bytes (cited_texts[].path), and the evidence-pinning
     drafts' digests from their bytes at the snapshot commit;
  6. the normative audit lists exactly the sentences normative_audit.py extracts
     from the cited -01 bytes, each mapped to at least one registry identifier,
     with exercised recomputed from the reverse view;
  7. mapping.json conforms to mapping.schema.json (jsonschema package; this script
     says so when it is not installed and the structural checks stand alone).
Exit code 0 only when every check holds.

    python3 mappings/receipt-verify-registry/validate_mapping.py [--mapping PATH]
"""
import hashlib, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normative_audit import extract as extract_normative

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
problems = []
mapping_path = os.path.join(HERE, "mapping.json")
if "--mapping" in sys.argv: mapping_path = sys.argv[sys.argv.index("--mapping") + 1]
doc = json.load(open(mapping_path))
COMMIT = doc["corpus_snapshot"]["commit"]

def snapshot_bytes(rel):
    r = subprocess.run(["git", "show", f"{COMMIT}:{rel}"], cwd=ROOT, capture_output=True)
    if r.returncode != 0:
        problems.append(f"git show {COMMIT[:12]}:{rel} failed: {r.stderr.decode().strip()}")
        return None
    return r.stdout

# 1. manifests at the snapshot commit
def manifest_ids(rel):
    data = snapshot_bytes(rel)
    if data is None: return None, None, None
    m = json.loads(data)
    if "accept_vectors" in m: ids = [v["id"] for v in m["accept_vectors"] + m["reject_vectors"]]
    else: ids = [v["id"] for v in m["vectors"]]
    return ids, hashlib.sha256(data).hexdigest(), m
for name, c in doc["corpora"].items():
    ids, digest, m = manifest_ids(c["manifest"])
    if ids is None: continue
    if c["manifest_sha256"] != digest: problems.append(f"{name}: manifest sha256 at snapshot {digest} != recorded {c['manifest_sha256']}")
    mapped = [v["id"] for v in c["vectors"]]
    if c["vector_count"] != len(ids): problems.append(f"{name}: vector_count {c['vector_count']} != manifest {len(ids)}")
    if len(mapped) != c["vector_count"]: problems.append(f"{name}: {len(mapped)} mapped vectors != vector_count")
    if sorted(mapped) != sorted(ids): problems.append(f"{name}: mapped ids differ from manifest ids: {sorted(set(mapped) ^ set(ids))}")
    if name == "evidence-pinning-rev8" and m["header"]["vector_count"] != len(ids): problems.append("rev8 header.vector_count disagrees with its vectors")

# 2. requirement identifiers; 3. every vector linked or deferred
registry = {rid for d in doc["requirement_documents"].values() for rid in d["requirements"]}
external = set(doc["external_documents"])
deferred_count = 0
for name, c in doc["corpora"].items():
    for v in c["vectors"]:
        for r in v.get("requirements", []):
            if r["requirement"] not in registry: problems.append(f"{name}/{v['id']}: unknown requirement {r['requirement']}")
        for e in v.get("external_requirements", []):
            if e["requirement"] not in external: problems.append(f"{name}/{v['id']}: unknown external {e['requirement']}")
        if v.get("status") == "deferred":
            deferred_count += 1
            if v.get("requirements"): problems.append(f"{name}/{v['id']}: deferred vector carries requirement coverage")
            if not isinstance(v.get("reason"), str) or not v["reason"].strip(): problems.append(f"{name}/{v['id']}: deferred without a reason")
        elif not v.get("requirements"):
            problems.append(f"{name}/{v['id']}: no requirement link and not deferred")
in_reverse = {rid for view in doc["reverse_view"].values() for rid in view["requirements"]}
for rid in registry - in_reverse: problems.append(f"registry requirement missing from the reverse view: {rid}")
if doc["totals"].get("deferred") != deferred_count: problems.append(f"totals.deferred {doc['totals'].get('deferred')} != {deferred_count}")

# 4. reverse view MUST EQUAL the forward view scoped to the corpora it names
rank = {"not covered": 0, "partial": 1, "covered": 2}
def check_summary(label, s, rows, key):
    counts = {"covered": 0, "partial": 0, "not covered": 0}
    for row in rows.values(): counts[row[key]] += 1
    if (s["requirements"], s["covered"], s["partial"], s["not_covered"]) != (len(rows), counts["covered"], counts["partial"], counts["not covered"]):
        problems.append(f"{label}: summary counts disagree with rows")
    if sorted(s["not_covered_list"]) != sorted(rid for rid, row in rows.items() if row[key] == "not covered"):
        problems.append(f"{label}: not_covered_list disagrees with rows")
for doc_id, view in doc["reverse_view"].items():
    scope = view["corpora"]
    for name in scope:
        if name not in doc["corpora"]: problems.append(f"reverse {doc_id}: names unknown corpus {name}")
    doc_reqs = set(doc["requirement_documents"][doc_id]["requirements"])
    if set(view["requirements"]) != doc_reqs: problems.append(f"reverse {doc_id}: requirement set differs from the registry")
    sub = view.get("summary_excluding_not_normative")
    subscope = sub["corpora"] if sub else None
    if sub:
        for name in subscope:
            if doc["corpora"].get(name, {}).get("normative") is not True: problems.append(f"reverse {doc_id}: excluding-not-normative scope names a non-normative or unknown corpus {name}")
        if any(doc["corpora"][n]["normative"] for n in scope if n not in subscope) : pass
        for n in scope:
            if n not in subscope and doc["corpora"][n].get("normative") is True: problems.append(f"reverse {doc_id}: normative corpus {n} excluded from the normative-only count")
    for rid, row in view["requirements"].items():
        hits = []
        for name in scope:
            for v in doc["corpora"][name]["vectors"]:
                for r in v.get("requirements", []):
                    if r["requirement"] == rid: hits.append((name, v["id"], r["coverage"]))
        listed = [(h["corpus"], h["vector"], h["coverage"]) for h in row["vectors"]]
        if sorted(listed) != sorted(hits): problems.append(f"reverse {rid}: listed hits {sorted(listed)} != scoped forward hits {sorted(hits)}")
        best = max((rank[h[2]] for h in hits), default=0)
        if rank[row["coverage"]] != best: problems.append(f"reverse {rid}: coverage {row['coverage']} != best of the scoped forward hits")
        if sub:
            best2 = max((rank[h[2]] for h in hits if h[0] in subscope), default=0)
            if rank[row.get("coverage_excluding_not_normative", "")] != best2 if row.get("coverage_excluding_not_normative") in rank else True:
                problems.append(f"reverse {rid}: coverage_excluding_not_normative {row.get('coverage_excluding_not_normative')} != best of the normative-only hits")
        if row["text"] != doc["requirement_documents"][doc_id]["requirements"][rid]: problems.append(f"reverse {rid}: text differs from the registry")
    check_summary(f"reverse {doc_id}", view["summary"], view["requirements"], "coverage")
    if sub: check_summary(f"reverse {doc_id} (excluding not normative)", sub, view["requirements"], "coverage_excluding_not_normative")

# 5. digests recomputed from the cited bytes and from the snapshot
for key, t in doc["cited_texts"].items():
    p = os.path.join(ROOT, t["path"])
    if not os.path.exists(p): problems.append(f"cited text {key}: {t['path']} missing"); continue
    with open(p, "rb") as f: actual = hashlib.sha256(f.read()).hexdigest()
    if actual != t["sha256"]: problems.append(f"cited text {key}: sha256 of the cited bytes {actual} != cited_texts.sha256 {t['sha256']}")
    recorded = doc["requirement_documents"][key].get("sha256")
    if actual != recorded: problems.append(f"cited text {key}: sha256 of the cited bytes {actual} != requirement_documents.{key}.sha256 {recorded}")
for key, t in doc["requirement_documents"]["EP"]["texts"].items():
    data = snapshot_bytes(t["path"])
    if data is None: continue
    actual = hashlib.sha256(data).hexdigest()
    if actual != t["sha256"]: problems.append(f"EP text {key}: sha256 at snapshot {actual} != recorded")
tot = doc["totals"]
if tot["mapped_or_deferred"] != sum(c["vector_count"] for c in doc["corpora"].values()): problems.append("totals.mapped_or_deferred disagrees")
if len(COMMIT) != 40 or any(ch not in "0123456789abcdef" for ch in COMMIT): problems.append("corpus_snapshot.commit is not a 40-hex commit id")

# 6. normative audit re-extracted from the cited bytes
aud = doc.get("normative_audit")
if not aud: problems.append("normative_audit missing")
else:
    p = os.path.join(ROOT, aud["source"])
    if os.path.exists(p):
        expected = extract_normative(open(p, encoding="utf-8").read())
        listed = [(r["section"], r["text"]) for r in aud["sentences"]]
        if listed != expected: problems.append(f"normative_audit: listed sentences differ from the extraction ({len(listed)} listed, {len(expected)} extracted)")
        d01 = doc["reverse_view"]["D01"]["requirements"]
        for r in aud["sentences"]:
            if not r["requirements"]: problems.append(f"normative_audit sentence {r['n']}: no requirement assigned")
            for i in r["requirements"]:
                if i not in d01: problems.append(f"normative_audit sentence {r['n']}: unknown requirement {i}")
            ex = any(d01.get(i, {}).get("coverage") != "not covered" for i in r["requirements"] if i in d01)
            if r["exercised"] != ex: problems.append(f"normative_audit sentence {r['n']}: exercised {r['exercised']} != recomputed {ex}")
        s = aud["summary"]
        if (s["sentences"], s["exercised"], s["unexercised"]) != (len(aud["sentences"]), sum(1 for r in aud["sentences"] if r["exercised"]), sum(1 for r in aud["sentences"] if not r["exercised"])):
            problems.append("normative_audit: summary disagrees with rows")

# 7. schema
try:
    import jsonschema
    jsonschema.validate(doc, json.load(open(os.path.join(HERE, "mapping.schema.json"))))
    schema_note = "schema: valid (jsonschema)"
except ImportError:
    schema_note = "schema: jsonschema package not installed; structural checks only"
except Exception as e:
    problems.append(f"schema: {str(e).splitlines()[0]}")
    schema_note = "schema: INVALID"

for p in problems: print("PROBLEM:", p)
print(schema_note)
print("snapshot:", COMMIT[:12], "| counts:", {k: c["vector_count"] for k, c in doc["corpora"].items()}, "| total", tot["mapped_or_deferred"], "| deferred", tot.get("deferred"))
print("RESULT:", "OK" if not problems else f"{len(problems)} problem(s)")
sys.exit(0 if not problems else 1)
