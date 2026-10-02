#!/usr/bin/env python3
"""Negative controls for validate_mapping.py: deliberately broken copies of
mapping.json that the validator MUST reject (an unlinked vector; zeroed -01 and
mapping digests; a wrong snapshot commit; a missing audit source, alone and
combined with an unassigned sentence or a deleted audit row; an audit source
whose bytes do not match the recorded digest), plus the real file, which it
must accept. Exit 0 only when every case behaves as expected.

    python3 mappings/receipt-verify-registry/negative_controls.py
"""
import copy, json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
real = json.load(open(os.path.join(HERE, "mapping.json")))

def unlinked(d):
    v = d["corpora"]["v0.3-composed"]["vectors"][0]
    v["requirements"] = []; v.pop("status", None); v.pop("reason", None)   # a vector with no link and no deferral
    return d
def zeroed_digests(d):
    z = "0" * 64
    d["requirement_documents"]["D01"]["sha256"] = z
    d["requirement_documents"]["MAP"]["sha256"] = z
    for t in d["cited_texts"].values(): t["sha256"] = z
    return d
def wrong_commit(d):
    d["corpus_snapshot"]["commit"] = "0" * 40
    return d

def missing_audit_source(d):
    d["normative_audit"]["source"] = "mappings/receipt-verify-registry/cited/does-not-exist.txt"
    return d
def missing_source_unassigned(d):
    d = missing_audit_source(d)
    d["normative_audit"]["sentences"][5]["requirements"] = []      # the §4.1 IANA SHOULD row, unassigned
    return d
def missing_source_deleted_row(d):
    d = missing_audit_source(d)
    del d["normative_audit"]["sentences"][5]                       # the §4.1 IANA SHOULD row, deleted
    return d
def mismatched_audit_source(d):
    d["cited_texts"]["D01"]["sha256"] = "1" * 64                   # recorded digest no longer matches the bytes
    d["requirement_documents"]["D01"]["sha256"] = "1" * 64
    return d

CASES = [("real mapping.json (control)", lambda d: d, 0),
         ("missing audit source", missing_audit_source, 1),
         ("missing audit source + an unassigned sentence", missing_source_unassigned, 1),
         ("missing audit source + a deleted audit row", missing_source_deleted_row, 1),
         ("audit source present but its bytes do not match the recorded digest", mismatched_audit_source, 1),
         ("unlinked vector (no requirement link, not deferred)", unlinked, 1),
         ("zeroed -01 and mapping-document digests", zeroed_digests, 1),
         ("wrong corpus_snapshot.commit", wrong_commit, 1)]
bad = 0
with tempfile.TemporaryDirectory() as tmp:
    for label, mutate, want in CASES:
        path = os.path.join(tmp, "mapping.json")
        json.dump(mutate(copy.deepcopy(real)), open(path, "w"))
        r = subprocess.run([sys.executable, os.path.join(HERE, "validate_mapping.py"), "--mapping", path], capture_output=True, text=True)
        got = 0 if r.returncode == 0 else 1
        first = next((ln for ln in r.stdout.splitlines() if ln.startswith("PROBLEM")), "(no problem line)")
        ok = got == want
        bad += 0 if ok else 1
        print(("PASS" if ok else "FAIL") + f": {label} -> validator exit {r.returncode} (expected {'0' if want == 0 else 'non-zero'}); {first[:140]}")
print("RESULT:", "OK" if not bad else f"{bad} control(s) misbehaved")
sys.exit(0 if not bad else 1)
