#!/usr/bin/env python3
# evidence-pinning fixture generator rev 6 — reference (Python)
#
# NEW FILENAME per semantics_change_new_filename.md. Against the rev 5 generator
# this file adds one vector (evi-node-raw-not-hex, rev 6 Finding 27) and moves
# correct_root out of evi-root-mismatch-rejects's input into computed (rev 6 E-3).
# Both change what the emitted set means, so the filename changes with it.
#
# Spec bases (all re-derived from TKCollective/agentoracle-receipt-spec at build time):
#   drafts/evidence-pinning-02-review-draft.md
#     sha256 9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096
#   drafts/evidence-pinning-02-amendments-rev5-2026-09-06.md
#     sha256 1f901fd7d56fcfe9f858446e5b685b540b5904d6abcfb4b2509e1eb675aa1e51
#   drafts/evidence-pinning-02-amendments-rev6-2026-09-08.md
#     (rev 6; digest recorded in the emitted header at build time)
#
# THIS FILE IS NOT AN INDEPENDENT IMPLEMENTATION.
# The companion evidence-pinning-fixture-crosscheck.mjs is authored by the same party as this
# file and shares its interpretation of the spec. Agreement between the two
# is a cross-language check that catches language-specific defects (JSON key
# ordering, UTF-8 handling, hashing library differences). It does NOT
# establish independence. Independence for this section means a build from
# the specification text alone by a party with no access to this file --
# Michael or Pablo. See the header of the emitted evidence-pinning-fixtures-v2-rev5.json.

from __future__ import annotations
import hashlib, json, sys
from dataclasses import dataclass

LEAF_PREFIX = b"ao-evidence-leaf-v2"
NODE_PREFIX = b"ao-evidence-node-v1"
SEP = b"\x00"

def sha256_hex(data: bytes) -> str: return hashlib.sha256(data).hexdigest()

@dataclass(frozen=True)
class Entry:
    url: str
    snippet_sha256: str  # 64 lowercase hex; the digest of the retrieved bytes (§4.1.1)
    content_kind: str    # "snippet" | "excerpt" | "full_resource"
    retrieved_at: str    # RFC 3339 UTC, 3 fractional digits per project convention
    pinned: bool = True

# ---------- normative construction (rev 5) --------------------------------

# Rev 5 Finding 24a: distinctness on the four bound members
def check_distinct(entries):
    seen = set()
    for e in entries:
        key = (e.url, e.snippet_sha256, e.content_kind, e.retrieved_at)
        if key in seen: raise ValueError(f"duplicate bound tuple: {key}")
        seen.add(key)

# Rev 4 15c amended by rev 5 24c: four-term sort, all bytewise UTF-8
def sort_key(e: Entry):
    return (e.url.encode("utf-8"),
            e.snippet_sha256.encode("utf-8"),
            e.content_kind.encode("utf-8"),
            e.retrieved_at.encode("utf-8"))

# Rev 4 15a: leaf preimage binds four members, prefix ao-evidence-leaf-v2
def leaf(e: Entry) -> bytes:
    return hashlib.sha256(LEAF_PREFIX + SEP
                          + e.url.encode("utf-8") + SEP
                          + e.snippet_sha256.encode("utf-8") + SEP
                          + e.content_kind.encode("utf-8") + SEP
                          + e.retrieved_at.encode("utf-8")).digest()

# Base l.120-128 as amended by rev 6 Finding 27: interior node, odd promoted
# unchanged, children as the 32 RAW OCTETS of the child digests.
#
# The raw-octet choice is what rev 6 Finding 27 makes normative. Before rev 6 no
# sentence in the spec pinned it, and this file took raw octets without the text
# compelling it -- which is the gap Michael Msebenzi's independent build found.
# interior_hex below is the counter-construction: identical in every respect
# except that children enter as their 64 hex characters. It exists only to
# produce the differing root for evi-node-raw-not-hex, so an implementation that
# chose hex fails that vector on a concrete value.
def interior(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(NODE_PREFIX + SEP + left + SEP + right).digest()

def interior_hex(left: bytes, right: bytes) -> bytes:
    """NON-NORMATIVE counter-construction: children as 64 hex chars, UTF-8."""
    return hashlib.sha256(NODE_PREFIX + SEP
                          + left.hex().encode("utf-8") + SEP
                          + right.hex().encode("utf-8")).digest()

def _fold(level, node_fn):
    """Shared level-folding so normative and counter-construction cannot drift."""
    while len(level) > 1:
        nxt = []
        i = 0
        while i + 1 < len(level):
            nxt.append(node_fn(level[i], level[i+1])); i += 2
        if i < len(level):  # odd: promote unchanged
            nxt.append(level[i])
        level = nxt
    return level[0]

def root(entries):
    pinned = [e for e in entries if e.pinned]
    if not pinned: return None
    level = [leaf(e) for e in sorted(pinned, key=sort_key)]
    return _fold(level, interior).hex()

def root_hex_children(entries):
    """NON-NORMATIVE. Same set, same leaves, hex-encoded node children."""
    pinned = [e for e in entries if e.pinned]
    if not pinned: return None
    level = [leaf(e) for e in sorted(pinned, key=sort_key)]
    return _fold(level, interior_hex).hex()

def evidence_root(entries):
    check_distinct(entries)
    return root(entries)

# ---------- fixture set (fifteen vectors) ---------------------------------

# stable content bytes so the digests are reproducible from this file alone
def h(s: str) -> str: return sha256_hex(s.encode("utf-8"))

# Reusable material
URL_A = "https://example.org/a"
URL_B = "https://example.org/b"
URL_A_UPPER = "https://EXAMPLE.ORG/a"  # different bytes, same resource
CK = "snippet"
TS_1 = "2026-09-01T12:00:00.000Z"
TS_2 = "2026-09-02T12:00:00.000Z"
D_alpha = h("alpha")
D_beta  = h("beta")

def make_vectors():
    out = []

    # ---- five root-bearing relational vectors (rev 4 unchanged expectations) ----

    e_ord_1 = [Entry(URL_A, D_alpha, CK, TS_1), Entry(URL_B, D_beta, CK, TS_1)]
    e_ord_2 = list(reversed(e_ord_1))
    out.append(dict(id="evi-root-order-independent", designation="CANONICAL ORDER",
                    input=dict(set_1=[e.__dict__ for e in e_ord_1],
                               set_2=[e.__dict__ for e in e_ord_2]),
                    expect="identical evidence_root",
                    computed=dict(root_1=evidence_root(e_ord_1),
                                  root_2=evidence_root(e_ord_2))))

    e_odd = [Entry(URL_A, D_alpha, CK, TS_1),
             Entry(URL_B, D_beta, CK, TS_1),
             Entry("https://example.org/c", h("gamma"), CK, TS_1)]
    out.append(dict(id="evi-root-odd-promotion", designation="ODD NODE",
                    input=[e.__dict__ for e in e_odd],
                    expect="root matches promote-not-duplicate (three sorted leaves, third promoted unchanged)",
                    computed=dict(root=evidence_root(e_odd))))

    # hex-vs-raw: two roots that MUST differ.
    e_hex = [Entry(URL_A, D_alpha, CK, TS_1)]
    hex_root = evidence_root(e_hex)
    # counter-construction: identical set but leaf preimage uses 32 raw bytes of the digest
    raw_leaf = hashlib.sha256(LEAF_PREFIX + SEP
                              + URL_A.encode() + SEP
                              + bytes.fromhex(D_alpha) + SEP
                              + CK.encode() + SEP
                              + TS_1.encode()).digest().hex()
    # rev 6 Finding 27: the NODE-level analogue of evi-leaf-hex-not-raw.
    # Two pinned items form exactly one interior node, so this is the smallest
    # set on which raw-octet and hex-char children disagree. A one-item set
    # cannot detect the branch (root is the leaf, no node formed), which is why
    # the rev 5 set was blind to it.
    e_node = [Entry(URL_A, D_alpha, CK, TS_1), Entry(URL_B, D_beta, CK, TS_1)]
    _node_raw = evidence_root(e_node)
    _node_hex = root_hex_children(e_node)
    assert _node_raw != _node_hex, "raw and hex children must differ on a two-item set"
    out.append(dict(id="evi-node-raw-not-hex", designation="NODE PREIMAGE",
                    input=dict(sources=[e.__dict__ for e in e_node],
                               note="two pinned items form exactly one interior node; "
                                    "the raw-children form is normative per rev 6 Finding 27"),
                    expect="evidence_root equals normative_raw_children_root; "
                           "an implementation encoding node children as hex characters "
                           "computes non_normative_hex_children_root and fails this vector",
                    computed=dict(normative_raw_children_root=_node_raw,
                                  non_normative_hex_children_root=_node_hex,
                                  differ=(_node_raw != _node_hex))))

    out.append(dict(id="evi-leaf-hex-not-raw", designation="LEAF PREIMAGE",
                    input=dict(entry=e_hex[0].__dict__,
                               note="the raw-form counter-construction is non-normative and shown to demonstrate the difference"),
                    expect="hex form is normative; raw form produces a different root",
                    computed=dict(normative_hex_root=hex_root, non_normative_raw_root=raw_leaf,
                                  differ=(hex_root != raw_leaf))))

    e_snip_1 = [Entry(URL_A, h("alpha"), CK, TS_1)]
    e_snip_2 = [Entry(URL_A, h("alpha-modified"), CK, TS_1)]
    out.append(dict(id="evi-snippet-change-changes-root", designation="BINDING",
                    input=dict(set_1=[e.__dict__ for e in e_snip_1],
                               set_2=[e.__dict__ for e in e_snip_2]),
                    expect="roots differ",
                    computed=dict(root_1=evidence_root(e_snip_1),
                                  root_2=evidence_root(e_snip_2),
                                  differ=(evidence_root(e_snip_1) != evidence_root(e_snip_2)))))

    e_url_1 = [Entry(URL_A, D_alpha, CK, TS_1)]
    e_url_2 = [Entry(URL_A_UPPER, D_alpha, CK, TS_1)]
    out.append(dict(id="evi-url-normalization-changes-root", designation="BINDING",
                    input=dict(set_1=[e.__dict__ for e in e_url_1],
                               set_2=[e.__dict__ for e in e_url_2]),
                    expect="roots differ; unnormalized bytes are normative",
                    computed=dict(root_1=evidence_root(e_url_1),
                                  root_2=evidence_root(e_url_2),
                                  differ=(evidence_root(e_url_1) != evidence_root(e_url_2)))))

    # ---- duplicate-url-distinct-digest, restated by rev 4 with four-term sort ----
    e_dup = [Entry(URL_A, D_alpha, CK, TS_1), Entry(URL_A, D_beta, CK, TS_1)]
    e_dup_rev = list(reversed(e_dup))
    out.append(dict(id="evi-duplicate-url-distinct-digest", designation="CANONICAL ORDER",
                    input=dict(set_1=[e.__dict__ for e in e_dup],
                               set_2=[e.__dict__ for e in e_dup_rev]),
                    expect="deterministic order by the four-term key of §4.1.2; stable root",
                    computed=dict(root_1=evidence_root(e_dup),
                                  root_2=evidence_root(e_dup_rev),
                                  identical=(evidence_root(e_dup) == evidence_root(e_dup_rev)))))

    # ---- rev 4's two "leaf binds" vectors (differ on the two members added by 15a) ----
    e_ck_1 = [Entry(URL_A, D_alpha, "snippet",       TS_1)]
    e_ck_2 = [Entry(URL_A, D_alpha, "full_resource", TS_1)]
    out.append(dict(id="evi-leaf-binds-content-kind", designation="LEAF PREIMAGE",
                    input=dict(set_1=[e.__dict__ for e in e_ck_1],
                               set_2=[e.__dict__ for e in e_ck_2]),
                    expect="evidence_root differs",
                    computed=dict(root_1=evidence_root(e_ck_1),
                                  root_2=evidence_root(e_ck_2),
                                  differ=(evidence_root(e_ck_1) != evidence_root(e_ck_2)))))

    e_ra_1 = [Entry(URL_A, D_alpha, CK, TS_1)]
    e_ra_2 = [Entry(URL_A, D_alpha, CK, TS_2)]
    out.append(dict(id="evi-leaf-binds-retrieved-at", designation="LEAF PREIMAGE",
                    input=dict(set_1=[e.__dict__ for e in e_ra_1],
                               set_2=[e.__dict__ for e in e_ra_2]),
                    expect="evidence_root differs",
                    computed=dict(root_1=evidence_root(e_ra_1),
                                  root_2=evidence_root(e_ra_2),
                                  differ=(evidence_root(e_ra_1) != evidence_root(e_ra_2)))))

    # ---- rev 4's two order-tiebreak vectors ----
    e_tk_1 = [Entry(URL_A, D_alpha, "snippet", TS_1),
              Entry(URL_A, D_alpha, "excerpt", TS_1)]
    out.append(dict(id="evi-order-tiebreak-content-kind", designation="CANONICAL ORDER",
                    input=dict(set_1=[e.__dict__ for e in e_tk_1],
                               set_2=[e.__dict__ for e in reversed(e_tk_1)]),
                    expect="identical evidence_root both ways",
                    computed=dict(root_1=evidence_root(e_tk_1),
                                  root_2=evidence_root(list(reversed(e_tk_1))),
                                  identical=(evidence_root(e_tk_1) == evidence_root(list(reversed(e_tk_1)))))))

    e_tr_1 = [Entry(URL_A, D_alpha, CK, TS_1),
              Entry(URL_A, D_alpha, CK, TS_2)]
    out.append(dict(id="evi-order-tiebreak-retrieved-at", designation="CANONICAL ORDER",
                    input=dict(set_1=[e.__dict__ for e in e_tr_1],
                               set_2=[e.__dict__ for e in reversed(e_tr_1)]),
                    expect="identical evidence_root both ways",
                    computed=dict(root_1=evidence_root(e_tr_1),
                                  root_2=evidence_root(list(reversed(e_tr_1))),
                                  identical=(evidence_root(e_tr_1) == evidence_root(list(reversed(e_tr_1)))))))

    # ---- MALFORMED vectors (no root computed; produce the wrong shape and expect halt) ----
    out.append(dict(id="evi-set-retrieved-at-not-earliest-rejects", designation="MALFORMED",
                    input=dict(set_retrieved_at=TS_2,
                               sources=[Entry(URL_A, D_alpha, CK, TS_1).__dict__,
                                        Entry(URL_B, D_beta,  CK, TS_2).__dict__]),
                    expect="halt, malformed"))
    out.append(dict(id="evi-content-kind-absent-when-pinned-rejects", designation="MALFORMED",
                    input=dict(entry=dict(url=URL_A, snippet_sha256=D_alpha, retrieved_at=TS_1, pinned=True)),
                    expect="halt, malformed; diagnostic names the missing member, not a root mismatch"))
    out.append(dict(id="evi-resource-sha256-with-full-resource-rejects", designation="MALFORMED",
                    input=dict(entry=dict(url=URL_A, snippet_sha256=D_alpha, content_kind="full_resource",
                                          retrieved_at=TS_1, pinned=True, resource_sha256=D_alpha)),
                    expect="halt, malformed"))
    out.append(dict(id="evi-empty-set-rejects", designation="MALFORMED",
                    input=dict(evidence_set=dict(source_count=0, sources=[])),
                    expect="halt, malformed"))
    # rev 5 Finding 24
    out.append(dict(id="evi-duplicate-bound-tuple-rejects", designation="MALFORMED",
                    input=dict(sources=[Entry(URL_A, D_alpha, CK, TS_1).__dict__,
                                        Entry(URL_A, D_alpha, CK, TS_1).__dict__]),
                    expect="halt, malformed"))
    # rev 5 Finding 25 (literal required, not exemplary)
    out.append(dict(id="evi-unpinned-reason-outside-domain-rejects", designation="MALFORMED",
                    input=dict(entry=dict(url=URL_A, snippet_sha256=None, content_kind=None,
                                          retrieved_at=TS_1, pinned=False,
                                          unpinned_reason="content_not_retained")),
                    expect="halt, malformed"))

    # ---- twelve vectors carried unchanged from rev 4 "Retained unchanged" ----
    # No roots computed for these; they are per-item / verifier-side / count-shape rules.

    # Malformed: unpinned without a reason
    out.append(dict(id="evi-unpinned-without-reason-rejects", designation="MALFORMED",
                    input=dict(entry=dict(url=URL_A, snippet_sha256=None, content_kind=None,
                                          retrieved_at=TS_1, pinned=False)),
                    expect="halt, malformed"))
    # Malformed: source_count disagrees with sources.length
    out.append(dict(id="evi-source-count-mismatch-rejects", designation="MALFORMED",
                    input=dict(evidence_set=dict(source_count=3,
                                                 sources=[Entry(URL_A, D_alpha, CK, TS_1).__dict__,
                                                          Entry(URL_B, D_beta,  CK, TS_1).__dict__])),
                    expect="halt, malformed"))
    # Malformed: pinned_count disagrees with pinned entries
    out.append(dict(id="evi-count-inconsistency-rejects", designation="MALFORMED",
                    input=dict(evidence_set=dict(source_count=2, pinned_count=2,
                                                 sources=[Entry(URL_A, D_alpha, CK, TS_1).__dict__,
                                                          dict(url=URL_B, snippet_sha256=None,
                                                               content_kind=None, retrieved_at=TS_1,
                                                               pinned=False,
                                                               unpinned_reason="no_content_returned")])),
                    expect="halt, malformed"))
    # Malformed: non-null root with zero pinned
    out.append(dict(id="evi-root-with-zero-pinned-rejects", designation="MALFORMED",
                    input=dict(evidence_set=dict(pinned_count=0,
                                                 evidence_root="0"*64,
                                                 sources=[dict(url=URL_A, snippet_sha256=None,
                                                               content_kind=None, retrieved_at=TS_1,
                                                               pinned=False,
                                                               unpinned_reason="no_content_returned")])),
                    expect="halt, malformed"))
    # Malformed: null root with pinned_count > 0
    out.append(dict(id="evi-nonzero-pinned-null-root-rejects", designation="MALFORMED",
                    input=dict(evidence_set=dict(pinned_count=1, evidence_root=None,
                                                 sources=[Entry(URL_A, D_alpha, CK, TS_1).__dict__])),
                    expect="halt, malformed"))
    # Malformed: root not recomputable from sources
    _e = [Entry(URL_A, D_alpha, CK, TS_1)]
    # rev 6 E-3, airlock structural fix: correct_root moves from input to
    # computed. It sat on the permitted side of the airlock, so an independent
    # implementer saw one concrete normative root before fixing their own roots.
    # Michael disclosed it and did not consult it; moving the field means no
    # future run has to make that disclosure.
    out.append(dict(id="evi-root-mismatch-rejects", designation="MALFORMED",
                    input=dict(evidence_set=dict(pinned_count=1,
                                                 evidence_root="ff"*32,  # arbitrary non-matching
                                                 sources=[e.__dict__ for e in _e]),
                               note="the correct root for this input is in computed, "
                                    "not here: it is a normative root and belongs "
                                    "on the excluded side of the airlock"),
                    expect="halt, malformed",
                    computed=dict(correct_root=evidence_root(_e))))

    # Empty: zero pinned is legal, evidence_root null (rev 4 preserves base l.139-140)
    _e_empty = [dict(url=URL_A, snippet_sha256=None, content_kind=None, retrieved_at=TS_1,
                     pinned=False, unpinned_reason="no_content_returned")]
    out.append(dict(id="evi-empty-root-null", designation="EMPTY",
                    input=dict(evidence_set=dict(source_count=1, pinned_count=0,
                                                 sources=_e_empty)),
                    expect="evidence_root null; receipt well-formed"))

    # Additive: absent evidence_set resolves unknown, MUST NOT halt
    out.append(dict(id="evi-absent-unknown", designation="ADDITIVE",
                    input=dict(receipt_shape="no evidence_set member present"),
                    expect="unknown; MUST NOT halt"))

    # Completeness pair -- rev 4 pair rule stands; both MUST be adopted together
    _e_partial = [Entry(URL_A, D_alpha, CK, TS_1).__dict__,
                  Entry(URL_B, D_beta,  CK, TS_1).__dict__,
                  dict(url="https://example.org/c", snippet_sha256=None, content_kind=None,
                       retrieved_at=TS_1, pinned=False,
                       unpinned_reason="no_content_returned")]
    out.append(dict(id="evi-partial-resolves-unknown", designation="COMPLETENESS",
                    input=dict(evidence_set=dict(source_count=3, pinned_count=2,
                                                 fully_pinned=False, sources=_e_partial)),
                    expect="step resolves unknown; must_not: [\"valid\"] on the offline-recompute claim"))
    out.append(dict(id="evi-declared-partial-is-not-invalid", designation="COMPLETENESS",
                    input=dict(evidence_set=dict(source_count=3, pinned_count=2,
                                                 fully_pinned=False, sources=_e_partial)),
                    expect="receipt core-valid; NOT malformed; MUST NOT halt",
                    note="pair with evi-partial-resolves-unknown; rev 4 pair rule stands"))

    # UNKNOWN pair (verifier holds different / no candidate bytes)
    out.append(dict(id="evi-content-mismatch-unknown", designation="UNKNOWN",
                    input=dict(entry=Entry(URL_A, D_alpha, CK, TS_1).__dict__,
                               verifier_holds_bytes_for=URL_A,
                               verifier_recomputed_sha256=h("different-bytes")),
                    expect="unknown; MUST NOT halt; per-item reason content_differs (MUST per rev 5 Finding 17)"))
    out.append(dict(id="evi-content-not-held-unknown", designation="UNKNOWN",
                    input=dict(entry=Entry(URL_A, D_alpha, CK, TS_1).__dict__,
                               verifier_holds_bytes_for=None),
                    expect="unknown; per-item reason content_not_held (MUST per rev 5 Finding 17)"))

    return out

def emit():
    vectors = make_vectors()
    header = dict(
        title="evidence-pinning conformance fixtures (v2 preimage, four-term sort, rev 6 rules)",
        spec_bases=dict(
            review_draft_sha256="9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096",
            rev5_sha256="1f901fd7d56fcfe9f858446e5b685b540b5904d6abcfb4b2509e1eb675aa1e51",
            rev6_sha256="d62ded37dcf63f541e5b670b0cc0f7876e04a182064eb06a32af0037effaf026",
            review_draft_and_rev3_head="49b7d039576b17e39dd707c9f223de5670c9be86",
            fixture_set_committed_at="45d959d01ba011e71fa6a1de515d4b75b3a7eaa6",
            fixture_set_committed_note="cab4808700fa (rev 5 + fixture bundle) and 45d959d01ba0 (this fixture set) both post-date 49b7d039.",
        ),
        leaf_prefix="ao-evidence-leaf-v2",
        node_prefix="ao-evidence-node-v1",
        node_child_encoding=("raw-octets: in the interior node, left and right are the 32 raw "
                             "octets of the child digests, not their hexadecimal form "
                             "(rev 6 Finding 27). Before rev 6 the spec did not state this; "
                             "evi-node-raw-not-hex is the vector that detects the other branch."),
        leaf_member_encoding=("utf-8: leaf members enter as their UTF-8 bytes, and "
                              "snippet_sha256 as its 64 lowercase hex characters encoded UTF-8 "
                              "(rev 2 Finding 1, scoped to the leaf preimage)."),
        independence_disclosure=(
            "This fixture set was produced by evidence-pinning-fixture-generator.py. The Node "
            "cross-check in evidence-pinning-fixture-crosscheck.mjs is authored by the same party. "
            "Agreement between the two is a cross-language check that catches "
            "language-specific defects (JSON ordering, UTF-8 handling, hash "
            "library differences). It is NOT an independent implementation. "
            "Independence for this section means a build from the specification "
            "text alone by a party with no access to these files."),
        vector_count=len(vectors),
    )
    return dict(header=header, vectors=vectors)

if __name__ == "__main__":
    data = emit()
    json_bytes = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(json_bytes)
    if len(sys.argv) > 1 and sys.argv[1] == "--summary":
        sys.stderr.write(f"\nvectors: {data['header']['vector_count']}\n")
        sys.stderr.write(f"json sha256: {hashlib.sha256(json_bytes).hexdigest()}\n")
