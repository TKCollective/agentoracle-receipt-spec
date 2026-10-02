#!/usr/bin/env python3
"""Extract every normative sentence (MUST, MUST NOT, SHALL, SHALL NOT, SHOULD,
SHOULD NOT, REQUIRED, RECOMMENDED) from sections 3-7, 9 and 10 of the cited
draft-krausz-verification-state-01 text. Shared by generate_mapping.py (which
assigns each sentence to requirement identifiers) and validate_mapping.py
(which re-extracts from the cited bytes and checks nothing is missing).

Deterministic: the input is pinned by digest, so the sentence list is too.
"""
import re

SECTIONS = {"3", "4", "5", "6", "7", "9", "10"}   # top-level sections in scope
KEYWORDS = re.compile(r"\b(MUST NOT|MUST|SHALL NOT|SHALL|SHOULD NOT|SHOULD|REQUIRED|RECOMMENDED)\b")
HEADING = re.compile(r"^(\d+)(\.\d+)*\.\s{2}\S")
PAGE_NOISE = re.compile(r"^(Krausz\s+Expires|Internet-Draft\s)")

def _rows_of_table(lines):
    """Join the wrapped cells of one ASCII-table row into a single string."""
    rows, cur = [], []
    for ln in lines:
        if ln.startswith("+"):
            if cur: rows.append(cur); cur = []
        elif ln.startswith("|"):
            cur.append(ln)
    if cur: rows.append(cur)
    out = []
    for row in rows:
        cells = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in row]
        ncol = max(len(c) for c in cells)
        merged = []
        for i in range(ncol):
            merged.append(" ".join(c[i] for c in cells if i < len(c) and c[i]))
        out.append(" | ".join(m for m in merged if m))
    return out

def extract(text):
    """Return [(section, sentence)] for every normative sentence in scope, in document order."""
    lines = text.split("\n")
    section = None
    paras, buf, table = [], [], []
    def flush():
        nonlocal buf, table
        if table:
            for r in _rows_of_table(table): paras.append((section, r, True))
            table = []
        if buf:
            paras.append((section, " ".join(s.strip() for s in buf), False)); buf = []
    for ln in lines:
        if "\f" in ln or PAGE_NOISE.match(ln.strip()): continue
        m = HEADING.match(ln)
        if m:
            flush(); section = ln.split("  ", 1)[0].strip().rstrip("."); continue
        st = ln.strip()
        if not st: flush(); continue
        if st.startswith(("+", "|")): table.append(st); continue
        buf.append(ln)
    flush()
    out = []
    for sec, para, is_table in paras:
        if sec is None or sec.split(".")[0] not in SECTIONS: continue
        if is_table:
            if KEYWORDS.search(para): out.append((sec, para))
            continue
        # split prose into sentences; keep list-item leaders ("*  alg: ...") with their sentence
        para = re.sub(r"\s+", " ", para).strip()
        for s in re.split(r"(?<=[.;])\s+(?=[A-Z*(\"])", para):
            s = s.strip().lstrip("* ").strip()
            if KEYWORDS.search(s): out.append((sec, s))
    return out

if __name__ == "__main__":
    import sys
    for sec, s in extract(open(sys.argv[1], encoding="utf-8").read()):
        print(f"[{sec}] {s}")
