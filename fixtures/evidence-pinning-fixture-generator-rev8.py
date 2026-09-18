#!/usr/bin/env python3
# evidence-pinning fixture generator rev 8 — reference (Python)
#
# NEW FILENAME per semantics_change_new_filename.md. Against the rev 7 generator
# this file changes two normative rules from a pinned-only reading to a
# whole-of-`sources` reading (rev 8 Findings 35 and 36), adds the form-rule scope
# sentence (Finding 37), renames two condition identifiers (Finding 38), drops the
# vector-uniqueness assertion on condition identifiers (Finding 39), and adds four
# vectors. Rev 7 and rev 8 are not interchangeable: three of the four new vectors
# are accepted by a rev 7-conformant implementation that read the rules as
# pinned-only. The filename changes with the semantics.
#
# Spec bases (all re-derived from TKCollective/agentoracle-receipt-spec at build time):
#   drafts/evidence-pinning-02-review-draft.md
#     sha256 9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096
#   drafts/evidence-pinning-02-amendments-rev5-2026-09-06.md
#     sha256 1f901fd7d56fcfe9f858446e5b685b540b5904d6abcfb4b2509e1eb675aa1e51
#   drafts/evidence-pinning-02-amendments-rev6-2026-09-08.md
#     sha256 d62ded37dcf63f541e5b670b0cc0f7876e04a182064eb06a32af0037effaf026
#   drafts/evidence-pinning-02-amendments-rev7-2026-09-09.md
#     sha256 6b13f6fc35d745c2642edcb52a2754f7cd43340ded3248b5d1ba70a431d6c037
#   drafts/evidence-pinning-02-amendments-rev8-2026-09-11.md
#     (rev 8; digest recorded in the emitted header at build time)
#
# THIS FILE IS NOT AN INDEPENDENT IMPLEMENTATION.
# The companion evidence-pinning-fixture-crosscheck-rev8.mjs is authored by the same party as this
# file and shares its interpretation of the spec. Agreement between the two
# is a cross-language check that catches language-specific defects (JSON key
# ordering, UTF-8 handling, hashing library differences). It does NOT
# establish independence. Independence for this section means a build from
# the specification text alone by a party with no access to this file --
# Michael or Pablo. See the header of the emitted evidence-pinning-fixtures-v2-rev8.json.

from __future__ import annotations
import hashlib, json, re, sys
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

# ---------- member access over both shapes --------------------------------
# Vectors carry pinned entries as Entry and unpinned entries as plain dicts,
# because an unpinned entry may OMIT snippet_sha256 and content_kind rather than
# carry them as null (rev 6 Finding 30). Every rule below that ranges over all of
# `sources` therefore reads members through these accessors, so absence and an
# explicit null are handled identically and neither shape gets a private path.

def _m(e, key, default=None):
    if isinstance(e, Entry): return getattr(e, key, default)
    return e.get(key, default)

def _is_pinned(e) -> bool:
    return _m(e, "pinned", True) is not False

# ---------- normative construction (rev 8) --------------------------------

# Rev 8 Finding 35 (restating rev 5 Finding 24a's §4.3 (a) without the leaf
# preimage): the entry-identity rule ranges over EVERY entry in `sources`.
# Two entries record the same retrieval when they are identical in url and
# retrieved_at and, where both are pinned, also identical in snippet_sha256 and
# content_kind. For an unpinned entry those two members distinguish nothing, so
# url with retrieved_at decides, and unpinned_reason is not part of identity.
def check_entry_identity(entries):
    buckets = {}
    for e in entries:
        buckets.setdefault((_m(e, "url"), _m(e, "retrieved_at")), []).append(e)
    for (url, ra), group in buckets.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if _is_pinned(a) and _is_pinned(b):
                    if (_m(a, "snippet_sha256"), _m(a, "content_kind")) == \
                       (_m(b, "snippet_sha256"), _m(b, "content_kind")):
                        raise ValueError(f"duplicate bound tuple: {(url, ra)}")
                else:
                    raise ValueError(f"duplicate bound tuple: {(url, ra)}")

# NON-NORMATIVE under rev 8. The pinned-only reading of the same rule, kept so
# the build can prove that the new vectors discriminate between the two readings
# instead of asserting that they do. See assert_scope_discriminating.
def check_entry_identity_pinned_only(entries):
    seen = set()
    for e in entries:
        if not _is_pinned(e): continue
        key = (_m(e, "url"), _m(e, "snippet_sha256"), _m(e, "content_kind"), _m(e, "retrieved_at"))
        if key in seen: raise ValueError(f"duplicate bound tuple: {key}")
        seen.add(key)

# Rev 8 Finding 36: the set-level retrieved_at MUST equal the bytewise-least
# retrieved_at among ALL entries in `sources`, comparing UTF-8 bytes as carried.
# Well-defined because `sources` is non-empty (rev 4 l.273-276) and every entry
# carries the member (base l.91).
def set_retrieved_at(entries) -> str:
    return min((_m(e, "retrieved_at") for e in entries), key=lambda s: s.encode("utf-8"))

# NON-NORMATIVE under rev 8: the pinned-only domain, for the same reason.
def set_retrieved_at_pinned_only(entries):
    vals = [_m(e, "retrieved_at") for e in entries if _is_pinned(e)]
    if not vals: return None
    return min(vals, key=lambda s: s.encode("utf-8"))

# Rev 8 Finding 37: the canonical-form rule of rev 6 Finding 32 ranges over every
# entry in `sources`, pinned and unpinned alike, and is evaluated before any
# branch on `pinned`.
_CANONICAL_RETRIEVED_AT = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

def retrieved_at_is_canonical(value) -> bool:
    return isinstance(value, str) and bool(_CANONICAL_RETRIEVED_AT.match(value))

def first_noncanonical_retrieved_at(entries, pinned_only: bool = False):
    for e in entries:
        if pinned_only and not _is_pinned(e): continue
        v = _m(e, "retrieved_at")
        if not retrieved_at_is_canonical(v): return e
    return None

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
    pinned = [e for e in entries if _is_pinned(e)]
    if not pinned: return None
    level = [leaf(e) for e in sorted(pinned, key=sort_key)]
    return _fold(level, interior).hex()

def root_hex_children(entries):
    """NON-NORMATIVE. Same set, same leaves, hex-encoded node children."""
    pinned = [e for e in entries if _is_pinned(e)]
    if not pinned: return None
    level = [leaf(e) for e in sorted(pinned, key=sort_key)]
    return _fold(level, interior_hex).hex()

def evidence_root(entries):
    check_entry_identity(entries)
    return root(entries)

# ---------- fixture set ---------------------------------------------------
# The vector count is not written anywhere in this file. It is DERIVED by
# equality from len(make_vectors()) at emit time (header.vector_count), and every
# group count in the README is derived the same way by scope-census below.

# stable content bytes so the digests are reproducible from this file alone
def h(s: str) -> str: return sha256_hex(s.encode("utf-8"))

# Reusable material
URL_A = "https://example.org/a"
URL_B = "https://example.org/b"
URL_A_UPPER = "https://EXAMPLE.ORG/a"  # different bytes, same resource
CK = "snippet"
TS_1 = "2026-09-01T12:00:00.000Z"
TS_2 = "2026-09-02T12:00:00.000Z"
# rev 8: bytewise-least of the three, and used only on unpinned entries, so the
# set-level minimum of Finding 36 falls outside the pinned subset.
TS_0 = "2026-08-31T12:00:00.000Z"
# rev 8 Finding 37: same instant as TS_1, zero fractional digits, carried on an
# unpinned entry.
TS_1_NONCANONICAL = "2026-09-01T12:00:00Z"
assert TS_0.encode() < TS_1.encode() < TS_2.encode()

def unpinned(url: str, retrieved_at: str, reason: str = "no_content_returned",
             explicit_nulls: bool = True) -> dict:
    """An unpinned `sources` entry. rev 4 l.294-296: content_kind is ABSENT on an
    unpinned entry, not null. snippet_sha256 is null (rev 4 l.294-296 / base l.99-100)."""
    e = dict(url=url, retrieved_at=retrieved_at, pinned=False, unpinned_reason=reason)
    if explicit_nulls: e["snippet_sha256"] = None
    return e
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
    out.append(dict(id="evi-node-child-encoding", designation="NODE PREIMAGE",
                    input=dict(sources=[e.__dict__ for e in e_node],
                               note="two pinned items form exactly one interior node, so the "
                                    "node child encoding is observable on a concrete value"),
                    expect="evidence_root MUST equal normative_root and MUST NOT equal "
                           "counter_construction_root. The encoding is stated normatively "
                           "in the specification and is deliberately not restated here.",
                    computed=dict(normative_root=_node_raw,
                                  counter_construction_root=_node_hex,
                                  differ=(_node_raw != _node_hex))))

    out.append(dict(id="evi-leaf-member-encoding", designation="LEAF PREIMAGE",
                    input=dict(entry=e_hex[0].__dict__,
                               note="the leaf member encoding is observable on a concrete value; "
                                    "the counter-construction differs only in that encoding"),
                    expect="evidence_root MUST equal normative_root and MUST NOT equal "
                           "counter_construction_root. The encoding is stated normatively "
                           "in the specification and is deliberately not restated here.",
                    computed=dict(normative_root=hex_root,
                                  counter_construction_root=raw_leaf,
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
    # rev 8 Finding 38 rename: set_retrieved_at_not_first_in_canonical_order ->
    # set_retrieved_at_not_bytewise_least. The rev 7 identifier borrowed "canonical
    # order", which is §4.1.2's pinned-only sort, for a set-level comparison.
    out.append(dict(id="evi-set-retrieved-at-not-earliest-rejects", designation="MALFORMED", condition="set_retrieved_at_not_bytewise_least",
                    input=dict(set_retrieved_at=TS_2,
                               sources=[Entry(URL_A, D_alpha, CK, TS_1).__dict__,
                                        Entry(URL_B, D_beta,  CK, TS_2).__dict__]),
                    expect="halt, malformed"))
    out.append(dict(id="evi-content-kind-absent-when-pinned-rejects", designation="MALFORMED", condition="content_kind_absent_when_pinned",
                    input=dict(entry=dict(url=URL_A, snippet_sha256=D_alpha, retrieved_at=TS_1, pinned=True)),
                    expect="halt, malformed; diagnostic names the missing member, not a root mismatch"))
    out.append(dict(id="evi-resource-sha256-with-full-resource-rejects", designation="MALFORMED", condition="snippet_digest_present_for_full_resource",
                    input=dict(entry=dict(url=URL_A, snippet_sha256=D_alpha, content_kind="full_resource",
                                          retrieved_at=TS_1, pinned=True, resource_sha256=D_alpha)),
                    expect="halt, malformed"))
    # rev 8 Finding 38 rename: pinned_set_empty -> evidence_set_names_no_sources.
    # The trigger is an empty `sources` array or `source_count` of zero (rev 4
    # l.273-276), not an empty pinned subset, which is legal (base l.139-140).
    # The new name is taken from rev 4 l.281-282's own sentence.
    out.append(dict(id="evi-empty-set-rejects", designation="MALFORMED", condition="evidence_set_names_no_sources",
                    input=dict(evidence_set=dict(source_count=0, sources=[])),
                    expect="halt, malformed"))
    # rev 5 Finding 24
    out.append(dict(id="evi-duplicate-bound-tuple-rejects", designation="MALFORMED", condition="duplicate_bound_tuple",
                    input=dict(sources=[Entry(URL_A, D_alpha, CK, TS_1).__dict__,
                                        Entry(URL_A, D_alpha, CK, TS_1).__dict__]),
                    expect="halt, malformed"))
    # rev 5 Finding 25 (literal required, not exemplary)
    out.append(dict(id="evi-unpinned-reason-outside-domain-rejects", designation="MALFORMED", condition="unpinned_reason_outside_domain",
                    input=dict(entry=dict(url=URL_A, snippet_sha256=None, content_kind=None,
                                          retrieved_at=TS_1, pinned=False,
                                          unpinned_reason="content_not_retained")),
                    expect="halt, malformed"))

    # ---- twelve vectors carried unchanged from rev 4 "Retained unchanged" ----
    # No roots computed for these; they are per-item / verifier-side / count-shape rules.

    # Malformed: unpinned without a reason
    out.append(dict(id="evi-unpinned-without-reason-rejects", designation="MALFORMED", condition="unpinned_without_reason",
                    input=dict(entry=dict(url=URL_A, snippet_sha256=None, content_kind=None,
                                          retrieved_at=TS_1, pinned=False)),
                    expect="halt, malformed"))
    # Malformed: source_count disagrees with sources.length
    out.append(dict(id="evi-source-count-mismatch-rejects", designation="MALFORMED", condition="source_count_disagrees_with_sources",
                    input=dict(evidence_set=dict(source_count=3,
                                                 sources=[Entry(URL_A, D_alpha, CK, TS_1).__dict__,
                                                          Entry(URL_B, D_beta,  CK, TS_1).__dict__])),
                    expect="halt, malformed"))
    # Malformed: pinned_count disagrees with pinned entries
    out.append(dict(id="evi-count-inconsistency-rejects", designation="MALFORMED", condition="pinned_count_disagrees_with_pinned_entries",
                    input=dict(evidence_set=dict(source_count=2, pinned_count=2,
                                                 sources=[Entry(URL_A, D_alpha, CK, TS_1).__dict__,
                                                          dict(url=URL_B, snippet_sha256=None,
                                                               content_kind=None, retrieved_at=TS_1,
                                                               pinned=False,
                                                               unpinned_reason="no_content_returned")])),
                    expect="halt, malformed"))
    # Malformed: non-null root with zero pinned
    out.append(dict(id="evi-root-with-zero-pinned-rejects", designation="MALFORMED", condition="root_present_with_zero_pinned",
                    input=dict(evidence_set=dict(pinned_count=0,
                                                 evidence_root="0"*64,
                                                 sources=[dict(url=URL_A, snippet_sha256=None,
                                                               content_kind=None, retrieved_at=TS_1,
                                                               pinned=False,
                                                               unpinned_reason="no_content_returned")])),
                    expect="halt, malformed"))
    # Malformed: null root with pinned_count > 0
    out.append(dict(id="evi-nonzero-pinned-null-root-rejects", designation="MALFORMED", condition="root_null_with_pinned_entries",
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
    out.append(dict(id="evi-root-mismatch-rejects", designation="MALFORMED", condition="root_not_recomputable_from_sources",
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

    # ==================== rev 7 additions ====================
    # Three rules rev 6 states that the rev 6 set does not exercise. Each was
    # found by Michael Msebenzi against the rev 6 run (2026-09-09).

    # rev 7 Finding 33a — no rev 6 vector expects an affirmative resolution.
    # Fifteen expect a halt, four expect `unknown`, none expect `resolved`.
    # This is the only rule in rev 6 that changes an output value for a
    # CONFORMANT input, and the shipped set could not tell whether an
    # implementation emits the right token or an arbitrary one.
    _e_res = [Entry(URL_A, D_alpha, CK, TS_1), Entry(URL_B, D_beta, CK, TS_1)]
    out.append(dict(id="evi-step-resolves-affirmatively", designation="RESOLUTION",
                    input=dict(evidence_set=dict(source_count=2, pinned_count=2,
                                                 sources=[e.__dict__ for e in _e_res]),
                               verifier_holds_bytes_for=[URL_A, URL_B],
                               content_matches=True),
                    expect="step resolves `resolved` (rev 6 Finding 29): not `unknown`, not a halt",
                    computed=dict(evidence_root=evidence_root(_e_res))))

    # rev 7 Finding 33b — the absent limb of rev 6 Finding 30's equivalence.
    # All seven unpinned entries in the rev 6 set carry an explicit null and
    # none omits the key, so only half the equivalence was exercised. The
    # failure this guards: an implementation that requires the member to be
    # present-and-null and rejects omission.
    #
    # NOT root-bearing, deliberately. Only pinned entries form leaves, so the
    # root here is a function of the single pinned entry and would equal the
    # explicit-null counterpart BY CONSTRUCTION. Asserting that equality would
    # assert something about this generator, not about the specification.
    out.append(dict(id="evi-unpinned-members-absent-accepted", designation="ADDITIVE",
                    input=dict(evidence_set=dict(
                        source_count=2, pinned_count=1,
                        sources=[Entry(URL_A, D_alpha, CK, TS_1).__dict__,
                                 # snippet_sha256 and content_kind OMITTED, not null
                                 dict(url=URL_B, retrieved_at=TS_1, pinned=False,
                                      unpinned_reason="no_content_returned")])),
                    expect="accepted; an omitted member is equivalent to an explicit null "
                           "on an unpinned entry (rev 6 Finding 30). Not root-bearing: see "
                           "rev 7 Finding 33b."))

    # rev 7 Finding 33c — rev 6 Finding 32's canonical-form rejection fires on
    # no rev 6 input, because both retrieved_at literals in the set are already
    # canonical. The zero-fractional-digit spelling is chosen as the
    # counter-example because it is the form a reader is most likely to assume
    # is canonical: a checker written against "RFC 3339 with Z" that does not
    # read the exactly-three-digits clause accepts it.
    out.append(dict(id="evi-retrieved-at-noncanonical-rejects", designation="MALFORMED",
                    condition="retrieved_at_not_canonical_form",
                    input=dict(entry=dict(url=URL_A, snippet_sha256=D_alpha, content_kind=CK,
                                          retrieved_at="2026-09-01T12:00:00Z", pinned=True)),
                    expect="halt, malformed; reported condition equals "
                           "retrieved_at_not_canonical_form"))

    # ==================== rev 8 additions ====================
    # Four vectors for the two scope rulings. The rev 7 set of 32 cannot fail on
    # any of them: its only duplicate pair is two pinned entries, its only
    # non-canonical retrieved_at is on a pinned entry, and every set-level
    # retrieved_at comparison in it has both entries pinned. Michael Msebenzi's
    # rev 7 run and Pablo Play's rev 7 read diverged on both rules and the set
    # agreed with both, which is what these four close.
    #
    # assert_scope_discriminating below PROVES the discrimination rather than
    # asserting it in prose: each of the first three is run against both readings
    # and the build fails if they agree.

    # rev 8 Finding 35 — two unpinned entries recording one retrieval. They differ
    # only in unpinned_reason, which is not part of entry identity.
    _dup_unpinned = [unpinned(URL_A, TS_1, "no_content_returned"),
                     unpinned(URL_A, TS_1, "provider_metadata_only")]
    out.append(dict(id="evi-duplicate-unpinned-entries-rejects", designation="MALFORMED",
                    condition="duplicate_bound_tuple",
                    input=dict(evidence_set=dict(source_count=2, pinned_count=0,
                                                 fully_pinned=False, evidence_root=None,
                                                 retrieved_at=TS_1,
                                                 sources=_dup_unpinned)),
                    expect="halt, malformed; reported condition equals duplicate_bound_tuple. "
                           "The domain of the entry-identity rule is stated normatively in "
                           "the specification and is deliberately not restated here."))

    # rev 8 Finding 37 — the non-canonical retrieved_at sits on the unpinned entry.
    # One pinned entry is present so pinned_count is non-zero and the halt cannot
    # be attributed to a zero-pinned set.
    _noncanon = [Entry(URL_A, D_alpha, CK, TS_1),
                 unpinned(URL_B, TS_1_NONCANONICAL)]
    out.append(dict(id="evi-unpinned-retrieved-at-noncanonical-rejects", designation="MALFORMED",
                    condition="retrieved_at_not_canonical_form",
                    input=dict(evidence_set=dict(source_count=2, pinned_count=1,
                                                 fully_pinned=False,
                                                 retrieved_at=TS_1,
                                                 sources=[_noncanon[0].__dict__, _noncanon[1]])),
                    expect="halt, malformed; reported condition equals "
                           "retrieved_at_not_canonical_form. Which entries the form rule "
                           "ranges over is stated normatively in the specification and is "
                           "deliberately not restated here."))

    # rev 8 Finding 36 accept limb — the bytewise-least retrieved_at in the set is
    # carried by an unpinned entry, and the set-level member equals it. Root-bearing:
    # the root is a real normative value over the pinned subset, and it is exactly
    # the value an implementation that mixed the two domains would still get right,
    # which is why the set-level member and not the root is what this vector turns on.
    _mixed = [Entry(URL_A, D_alpha, CK, TS_1), unpinned(URL_B, TS_0)]
    _mixed_least = set_retrieved_at(_mixed)          # DERIVED, not written
    assert _mixed_least == TS_0
    out.append(dict(id="evi-set-retrieved-at-equals-unpinned-value", designation="SET SCOPE",
                    input=dict(evidence_set=dict(source_count=2, pinned_count=1,
                                                 fully_pinned=False,
                                                 retrieved_at=_mixed_least,
                                                 sources=[_mixed[0].__dict__, _mixed[1]]),
                               note="the bytewise-least retrieved_at in this set is carried by "
                                    "an unpinned entry"),
                    expect="accepted; receipt well-formed; the step MUST NOT halt on the "
                           "set-level retrieved_at. The domain of that comparison is stated "
                           "normatively in the specification and is deliberately not "
                           "restated here.",
                    computed=dict(evidence_root=evidence_root(_mixed))))

    # rev 8 Finding 36 reject limb — same set, and the set-level member is the
    # bytewise-least value among the pinned entries instead.
    _mixed_pinned_least = set_retrieved_at_pinned_only(_mixed)   # DERIVED, not written
    assert _mixed_pinned_least == TS_1 and _mixed_pinned_least != _mixed_least
    out.append(dict(id="evi-set-retrieved-at-above-unpinned-value-rejects", designation="MALFORMED",
                    condition="set_retrieved_at_not_bytewise_least",
                    input=dict(evidence_set=dict(source_count=2, pinned_count=1,
                                                 fully_pinned=False,
                                                 retrieved_at=_mixed_pinned_least,
                                                 sources=[_mixed[0].__dict__, _mixed[1]]),
                               note="an entry in this set carries a bytewise-lesser "
                                    "retrieved_at than the set-level member"),
                    expect="halt, malformed; reported condition equals "
                           "set_retrieved_at_not_bytewise_least. The domain of the "
                           "comparison is stated normatively in the specification and is "
                           "deliberately not restated here."))

    return out

# rev 7 Finding 34 enforcement. A vector that names its own answer has measured
# nothing, so naming it fails the build rather than shipping.
_RESOLUTION_TOKENS = ("raw", "hex", "not-hex", "not_hex", "octet", "normative_raw",
                      "normative_hex", "non_normative")

def assert_no_disclosure(vectors):
    bad = []
    for v in vectors:
        vid = v["id"]
        for tok in _RESOLUTION_TOKENS:
            if tok in vid.lower():
                bad.append(f"id {vid!r} contains resolution token {tok!r}")
        for key in (v.get("computed") or {}):
            for tok in _RESOLUTION_TOKENS:
                if tok in key.lower():
                    bad.append(f"{vid}: computed key {key!r} contains resolution token {tok!r}")
    if bad:
        raise SystemExit("rev 7 Finding 34 violation:\n  " + "\n  ".join(bad))

# rev 8 Finding 38: identifiers superseded by this revision. Published, not
# dropped: a run against rev 7 reported the left-hand value, and a reader
# comparing runs must be able to map it.
SUPERSEDED_CONDITIONS = {
    "pinned_set_empty": "evidence_set_names_no_sources",
    "set_retrieved_at_not_first_in_canonical_order": "set_retrieved_at_not_bytewise_least",
}

def assert_conditions_complete(vectors):
    """Every MALFORMED vector names exactly one condition (rev 7 Finding 33).

    rev 8 Finding 39: the uniqueness check rev 7 shipped alongside this one is
    REMOVED. It asserted that no two vectors name the same condition, which was
    true of the rev 7 set by accident of construction rather than by rule. rev 8
    deliberately injects three already-vectored conditions on a different entry
    class, so uniqueness would fail a correct set. What replaces it: every named
    condition must be a live identifier, never a superseded one.
    """
    missing = [v["id"] for v in vectors
               if v["designation"] == "MALFORMED" and not v.get("condition")]
    if missing:
        raise SystemExit("rev 7 Finding 33 violation: MALFORMED without condition:\n  "
                         + "\n  ".join(missing))
    stale = sorted({v["condition"] for v in vectors
                    if v.get("condition") in SUPERSEDED_CONDITIONS})
    if stale:
        raise SystemExit("rev 8 Finding 38 violation: superseded condition identifier in "
                         f"use: {stale}")

def assert_scope_discriminating(vectors):
    """rev 8: prove the four new vectors distinguish the two readings.

    Each check runs the vector's own input under BOTH the whole-of-`sources`
    reading and the pinned-only reading and fails the build if they agree. A
    vector that cannot fail on the defect it was added for is not evidence, and
    this is the check that would have caught the rev 7 set's blindness.
    """
    by_id = {v["id"]: v for v in vectors}
    fails = []

    def sources_of(vid):
        return by_id[vid]["input"]["evidence_set"]["sources"]

    def raises(fn, arg):
        try:
            fn(arg); return False
        except ValueError:
            return True

    # 1. duplicate unpinned pair: halts under rev 8, accepted under pinned-only.
    s = sources_of("evi-duplicate-unpinned-entries-rejects")
    if not raises(check_entry_identity, s):
        fails.append("evi-duplicate-unpinned-entries-rejects: rev 8 identity rule does not halt")
    if raises(check_entry_identity_pinned_only, s):
        fails.append("evi-duplicate-unpinned-entries-rejects: pinned-only reading also halts, "
                     "so the vector does not discriminate")

    # 2. non-canonical retrieved_at on the unpinned entry.
    s = sources_of("evi-unpinned-retrieved-at-noncanonical-rejects")
    if first_noncanonical_retrieved_at(s) is None:
        fails.append("evi-unpinned-retrieved-at-noncanonical-rejects: no non-canonical value found")
    if first_noncanonical_retrieved_at(s, pinned_only=True) is not None:
        fails.append("evi-unpinned-retrieved-at-noncanonical-rejects: a pinned entry also "
                     "carries a non-canonical value, so the vector does not discriminate")

    # 3/4. the set-level pair: accept limb and reject limb turn on opposite
    # readings of the same set, so one of the two halts under either reading and
    # no implementation can pass both by mixing domains.
    acc = by_id["evi-set-retrieved-at-equals-unpinned-value"]["input"]["evidence_set"]
    rej = by_id["evi-set-retrieved-at-above-unpinned-value-rejects"]["input"]["evidence_set"]
    for label, es, want_all in (("accept limb", acc, True), ("reject limb", rej, False)):
        all_least = set_retrieved_at(es["sources"])
        pinned_least = set_retrieved_at_pinned_only(es["sources"])
        if all_least == pinned_least:
            fails.append(f"{label}: the two domains give the same value, so the vector "
                         "does not discriminate")
        if (es["retrieved_at"] == all_least) is not want_all:
            fails.append(f"{label}: set-level retrieved_at does not sit where the vector "
                         "requires it")
        if (es["retrieved_at"] == pinned_least) is want_all:
            fails.append(f"{label}: set-level retrieved_at does not sit where the vector "
                         "requires it under the pinned-only reading")

    if fails:
        raise SystemExit("rev 8 scope-discrimination failure:\n  " + "\n  ".join(fails))

def _entries_of(vector) -> list:
    found = []
    def _walk(node):
        if isinstance(node, dict):
            if "url" in node and "retrieved_at" in node: found.append(node)
            for val in node.values(): _walk(val)
        elif isinstance(node, list):
            for val in node: _walk(val)
    _walk(vector.get("input"))
    return found

def census(vectors) -> dict:
    """DERIVED group counts. Every number the README quotes comes from here, by
    equality from the emitted set, never written by hand (rev 7 E-4's class)."""
    root_bearing = [v for v in vectors if v.get("computed")]
    malformed = [v for v in vectors if v["designation"] == "MALFORMED"]
    overlap = [v for v in root_bearing if v in malformed]
    remaining = [v for v in vectors if v not in root_bearing and v not in malformed]
    root_values = sum(len([k for k in (v.get("computed") or {}) if "root" in k.lower()])
                      for v in vectors)
    # Entry census by walking the whole emitted tree for objects carrying both
    # `url` and `retrieved_at`, so no vector shape is privileged and nothing is
    # counted by hand. This is the census Michael Msebenzi reported against rev 7;
    # it is emitted here so a future run compares numbers instead of recounting.
    entries = []
    def _walk(node):
        if isinstance(node, dict):
            if "url" in node and "retrieved_at" in node:
                entries.append(node)
            for val in node.values(): _walk(val)
        elif isinstance(node, list):
            for val in node: _walk(val)
    for v in vectors:
        _walk(v.get("input"))
    n_unpinned = len([e for e in entries if e.get("pinned") is False])
    return dict(total=len(vectors), root_bearing=len(root_bearing),
                entry_objects=len(entries),
                entries_pinned=len(entries) - n_unpinned,
                entries_unpinned=n_unpinned,
                vectors_carrying_unpinned_entries=len(
                    [v for v in vectors
                     if any(e.get("pinned") is False for e in _entries_of(v))]),
                root_values=root_values, malformed=len(malformed),
                remaining=len(remaining), overlap=len(overlap),
                arithmetic=f"{len(root_bearing)} + {len(malformed)} + {len(remaining)} "
                           f"\u2212 {len(overlap)} = "
                           f"{len(root_bearing)+len(malformed)+len(remaining)-len(overlap)}",
                arithmetic_holds=(len(root_bearing) + len(malformed) + len(remaining)
                                  - len(overlap) == len(vectors)),
                conditions_named=sorted({v["condition"] for v in vectors if v.get("condition")}))

def emit():
    vectors = make_vectors()
    assert_no_disclosure(vectors)
    assert_conditions_complete(vectors)
    assert_scope_discriminating(vectors)
    header = dict(
        title="evidence-pinning conformance fixtures (v2 preimage, four-term sort, rev 8 rules)",
        superseded_conditions=SUPERSEDED_CONDITIONS,
        superseded_conditions_note=(
            "rev 8 Finding 38. A run against rev 7 reported the left-hand identifier; "
            "rev 8 requires the right-hand one. The old values are published as "
            "superseded rather than dropped so two runs can be compared. A vector "
            "naming a superseded identifier fails the build."),
        census_note=("header.census is DERIVED from the emitted vectors at build time "
                     "(see census() in the generator). No count in it is written by hand."),
        spec_bases=dict(
            review_draft_sha256="9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096",
            rev5_sha256="1f901fd7d56fcfe9f858446e5b685b540b5904d6abcfb4b2509e1eb675aa1e51",
            rev6_sha256="d62ded37dcf63f541e5b670b0cc0f7876e04a182064eb06a32af0037effaf026",
            rev7_sha256="6b13f6fc35d745c2642edcb52a2754f7cd43340ded3248b5d1ba70a431d6c037",
            rev8_sha256="a92c17e8240d8aaccd3ac1d74119a8ddb3095624eb677c914ee208168f5e961a",
            rev8_base_commit="3d0ec0e82229c1336340f0323d54904e5baf38b2",
            review_draft_and_rev3_head="49b7d039576b17e39dd707c9f223de5670c9be86",
            fixture_set_committed_at="45d959d01ba011e71fa6a1de515d4b75b3a7eaa6",
            fixture_set_committed_note="cab4808700fa (rev 5 + fixture bundle) and 45d959d01ba0 (this fixture set) both post-date 49b7d039.",
        ),
        leaf_prefix="ao-evidence-leaf-v2",
        node_prefix="ao-evidence-node-v1",
        # rev 7 Finding 34: these cited the governing text and DID restate the
        # resolution, which handed an implementer the answer the vectors exist to
        # check. They now cite and do not restate.
        node_child_encoding=("stated normatively in rev 6 Finding 27 (base l.101-104). "
                             "Deliberately not restated here: evi-node-child-encoding verifies "
                             "the choice, the specification states it (rev 7 Finding 34)."),
        leaf_member_encoding=("stated normatively in rev 2 Finding 1, scoped to the leaf "
                              "preimage. Deliberately not restated here: "
                              "evi-leaf-member-encoding verifies the choice (rev 7 Finding 34)."),
        independence_disclosure=(
            "This fixture set was produced by evidence-pinning-fixture-generator-rev8.py. The Node "
            "cross-check in evidence-pinning-fixture-crosscheck-rev8.mjs is authored by the same party. "
            "Agreement between the two is a cross-language check that catches "
            "language-specific defects (JSON ordering, UTF-8 handling, hash "
            "library differences). It is NOT an independent implementation. "
            "Independence for this section means a build from the specification "
            "text alone by a party with no access to these files."),
        vector_count=len(vectors),
        census=census(vectors),
    )
    return dict(header=header, vectors=vectors)

if __name__ == "__main__":
    data = emit()
    json_bytes = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(json_bytes)
    if len(sys.argv) > 1 and sys.argv[1] == "--summary":
        sys.stderr.write(f"\nvectors: {data['header']['vector_count']}\n")
        sys.stderr.write(f"json sha256: {hashlib.sha256(json_bytes).hexdigest()}\n")
