#!/usr/bin/env python3
"""Validate mapping.json against the corpus manifests and the schema.

Independent of the generator: it re-reads the manifests, and checks that
  1. every corpus's vector_count equals the manifest's count, and every mapped
     vector id exists in its manifest (and vice versa);
  2. every requirement identifier referenced exists in the registry, and every
     registry identifier appears in the reverse view;
  3. the reverse view EQUALS the forward view scoped to the corpora each view names
     (every hit, and the best coverage), recomputed here;
  4. every pinned text digest in the registry matches the file at this checkout;
  5. mapping.json conforms to mapping.schema.json when the `jsonschema` package
     is available (otherwise the structural checks above stand alone and this
     script says so).
Exit code 0 only when every check holds.

    python3 mappings/receipt-verify-registry/validate_mapping.py
"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
problems = []

def load(rel):
    with open(os.path.join(ROOT, rel), "rb") as f: data = f.read()
    return json.loads(data), hashlib.sha256(data).hexdigest()

doc = json.load(open(os.path.join(HERE, "mapping.json")))

# 1. counts and ids against the manifests
def manifest_ids(rel):
    m, digest = load(rel)
    if "accept_vectors" in m: ids = [v["id"] for v in m["accept_vectors"] + m["reject_vectors"]]
    else: ids = [v["id"] for v in m["vectors"]]
    return ids, digest, m
for name, c in doc["corpora"].items():
    ids, digest, m = manifest_ids(c["manifest"])
    if c["manifest_sha256"] != digest: problems.append(f"{name}: manifest sha256 {digest} != recorded {c['manifest_sha256']}")
    mapped = [v["id"] for v in c["vectors"]]
    if c["vector_count"] != len(ids): problems.append(f"{name}: vector_count {c['vector_count']} != manifest {len(ids)}")
    if len(mapped) != c["vector_count"]: problems.append(f"{name}: {len(mapped)} mapped vectors != vector_count")
    if sorted(mapped) != sorted(ids): problems.append(f"{name}: mapped ids differ from manifest ids: {sorted(set(mapped) ^ set(ids))}")
    if name == "evidence-pinning-rev8" and m["header"]["vector_count"] != len(ids): problems.append("rev8 header.vector_count disagrees with its vectors")

# 2. requirement identifiers
registry = {rid for d in doc["requirement_documents"].values() for rid in d["requirements"]}
external = set(doc["external_documents"])
for name, c in doc["corpora"].items():
    for v in c["vectors"]:
        for r in v.get("requirements", []):
            if r["requirement"] not in registry: problems.append(f"{name}/{v['id']}: unknown requirement {r['requirement']}")
        for e in v.get("external_requirements", []):
            if e["requirement"] not in external: problems.append(f"{name}/{v['id']}: unknown external {e['requirement']}")
        if v.get("status") == "deferred" and v.get("requirements"): problems.append(f"{name}/{v['id']}: deferred vector carries requirement coverage")
in_reverse = {rid for view in doc["reverse_view"].values() for rid in view["requirements"]}
for rid in registry - in_reverse: problems.append(f"registry requirement missing from the reverse view: {rid}")

# 3. reverse view MUST EQUAL the forward view scoped to the corpora it names
rank = {"not covered": 0, "partial": 1, "covered": 2}
for doc_id, view in doc["reverse_view"].items():
    scope = view["corpora"]
    for name in scope:
        if name not in doc["corpora"]: problems.append(f"reverse {doc_id}: names unknown corpus {name}")
    doc_reqs = set(doc["requirement_documents"][doc_id]["requirements"])
    if set(view["requirements"]) != doc_reqs: problems.append(f"reverse {doc_id}: requirement set differs from the registry")
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
    s = view["summary"]
    counts = {"covered": 0, "partial": 0, "not covered": 0}
    for row in view["requirements"].values(): counts[row["coverage"]] += 1
    if (s["requirements"], s["covered"], s["partial"], s["not_covered"]) != (len(view["requirements"]), counts["covered"], counts["partial"], counts["not covered"]):
        problems.append(f"reverse {doc_id}: summary counts disagree with rows")
    if sorted(s["not_covered_list"]) != sorted(rid for rid, row in view["requirements"].items() if row["coverage"] == "not covered"):
        problems.append(f"reverse {doc_id}: not_covered_list disagrees with rows")

# 4. pinned digests
for key, t in doc["requirement_documents"]["EP"]["texts"].items():
    with open(os.path.join(ROOT, t["path"]), "rb") as f: actual = hashlib.sha256(f.read()).hexdigest()
    if actual != t["sha256"]: problems.append(f"EP text {key}: sha256 {actual} != recorded")
tot = doc["totals"]
if tot["mapped_or_deferred"] != sum(c["vector_count"] for c in doc["corpora"].values()): problems.append("totals.mapped_or_deferred disagrees")

# 5. schema
try:
    import jsonschema
    jsonschema.validate(doc, json.load(open(os.path.join(HERE, "mapping.schema.json"))))
    schema_note = "schema: valid (jsonschema)"
except ImportError:
    schema_note = "schema: jsonschema package not installed; structural checks only"
except Exception as e:
    problems.append(f"schema: {e}")
    schema_note = "schema: INVALID"

for p in problems: print("PROBLEM:", p)
print(schema_note)
print("counts:", {k: c["vector_count"] for k, c in doc["corpora"].items()}, "| total", tot["mapped_or_deferred"])
print("RESULT:", "OK" if not problems else f"{len(problems)} problem(s)")
sys.exit(0 if not problems else 1)
