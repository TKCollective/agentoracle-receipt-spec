# Vector → requirement mapping (receipt-verify registry, methodology §2.7)

`mapping.json` states, for each published conformance vector in this repository
at commit `cbba94b7576cf2aec08c70aeb2899fdfa4d35c66`, which normative
requirement it exercises and whether the corresponding assertion is actually
executed by a published checker (**forward view**), and, for each in-scope
requirement, which vectors exercise it or that none does (**reverse view**).
It is written for the receipt-verify registry's axis §2.7 (*Vector requirement
mapping*, methodology v0.4.5 draft, unchanged from v0.4.1) and follows its
procedure: mapped vectors exist in the corpus, and requirements no vector
exercises are listed. The requirement identifiers are this mapping's own labels
for sentences in the cited texts at the recorded revision (none of the
specifications numbers its requirements); each label carries the sentence it
stands for, so a reader can check it against the text. Where a rule was amended
after the review draft, the identifier names the amending finding.

Revision 2 (2026-10-01) applies Michael Msebenzi's review of `b1da800`; the
changes are listed under *What changed in revision 2* below.

## Corpora

| Corpus | Manifest | Vectors | Normative | Requirement texts |
|---|---|---|---|---|
| `v0.3-composed` | `examples/v0.3-composed/vectors.json` | 11 | yes | `draft-krausz-verification-state-01`; README "Mycelium Trails" at `196df22b` |
| `v0.4-composed` | `examples/v0.4-composed/vectors.json` | 3 | yes | same |
| `evidence-pinning-rev8` | `fixtures/evidence-pinning-fixtures-v2-rev8.json` | 44 (FINAL) | yes | the evidence-pinning section: review draft + amendments rev5–rev8 at the digests the fixture header pins; rev2 and rev4 at this commit (digests recorded) |
| `rule2` | `conformance/vectors-rule2.json` | 9 | **NOT NORMATIVE** (the manifest's own label) | mapping `agentoracle-v0.3-2026-05-30`; `-01` §5 |
| `leaf-screen-halt` | `examples/conformance/delegation-chain-ref/leaf-screen-halt/vectors.json` | 1 | yes | deferred: its requirement text is third-party (`delegation-chain-ref-v1`) |

Every manifest and every evidence-pinning draft is read at the snapshot commit
with `git show`, never from the working tree. Not counted: the 7 vectors on the
unmerged v0.4 branch; the rev5–rev7 fixture files (superseded by rev8).

## Coverage vocabulary

Coverage is recorded only where an assertion is actually executed:

- **covered** — executed by a checker published with the corpus against the shipped file;
- **partial** — declared in the manifest and executed only by the emitter that produced it or by an external run, or the checker exercises part of the requirement;
- **not covered** — no executed assertion.

The reverse view takes the best coverage any vector gives a requirement within
the corpora it names. The rev8 cross-check
(`fixtures/evidence-pinning-fixture-crosscheck-rev8.mjs`) is, in its own
README's words, *not a conformance verifier*: it checks roots, census and
condition identifiers, so it can give *covered* only to root-construction rules
and to the four rev8 discriminating vectors; every halt or `unknown` expectation
is *partial* (executed by the emitter and by an external run) or *not covered*.
Requirements that live only in third-party texts (`action-ref-v1`,
`delegation-chain-ref-v1`, the Mycelium Provider protocol) are listed under
`external_documents` and never counted as coverage of the in-scope texts.

## Every vector is linked or deferred

Every vector carries at least one in-scope requirement link, or an explicit
`status: "deferred"` with a `reason`. Four vectors are deferred: `comp-r05` and
`comp-r06` (the decisive rule is third-party, `delegation-chain-ref-v1`),
`d1-no-receipt` (a service-level rule, not a format requirement; its runner
skips it) and `leaf-screen-halt` (third-party text). The schema and the
validator both enforce the rule.

## Two counts for `-01`

The `rule2` set keeps its manifest's NOT NORMATIVE label, so the reverse view
for `-01` reports two counts over its 58 requirements:

| Count | Corpora | covered | partial | not covered |
|---|---|---|---|---|
| all corpora (`summary`) | v0.3-composed, v0.4-composed, rule2 | 10 | 6 | 42 |
| excluding NOT NORMATIVE (`summary_excluding_not_normative`) | v0.3-composed, v0.4-composed | 3 | 5 | 50 |

Each row also carries `coverage_excluding_not_normative`. The rows that differ
between the two counts are the §5.1 table rows 1–6 and the two §5.2 rules that
only `rule2` exercises.

## Finding 1: `typ`

`-01` §4.1 names `typ: verification-receipt+jws`. The v0.3 fixtures use
`application/vnd.verification.v0.3+composed+jws` and the v0.4 fixtures (all 12
protected headers) use `application/vnd.verification.v0.4+composed+jws`;
neither matches `-01` §4.1, and no published checker asserts `typ`. The
requirement `D01-4.1-typ` is *not covered* and carries this note.

## Normative audit of `-01` §§3–7, 9, 10

`normative_audit.py` extracts every sentence of the cited `-01` text in
sections 3–7, 9 and 10 that carries MUST, MUST NOT, SHALL, SHALL NOT, SHOULD,
SHOULD NOT, REQUIRED or RECOMMENDED. `mapping.json` lists all 55 of them
under `normative_audit`, each mapped to one or more requirement identifiers;
10 are exercised by at least one vector (coverage covered or partial, all
corpora) and 45 are unexercised. The generator refuses to run if a
sentence is unassigned; the validator re-extracts from the cited bytes and
fails if the list differs. Obligations added in revision 2 from this audit:
`D01-4.1-iana-alg` (§4.1 SHOULD follow the IANA JOSE Algorithms registry),
`D01-6.1-reject-expired` (§6.1 table: MUST reject expired signatures),
`D01-9.1-no-mask-env-halt` (§9.1 MUST NOT mask an environment.* HALT),
`D01-9.1-env-terminal-first` (§9.1 MUST evaluate environment.* to its
terminal state first; SHALL NOT reach a verification.* state otherwise) and
`D01-9.2-unverifiable-mapping-hash-malformed` (§9.2 a relying party that
cannot verify the mapping hash MUST treat the receipt as malformed), each with
cross-references to the rows it overlaps; `D01-4.6-mapping-immutable` and
`D01-9.2-mapping-tampering` now carry the full sentence text.

## Cited bytes

`cited/` holds the bytes the `-01` and mapping-document digests are computed
over: `draft-krausz-verification-state-01.txt` (fetched 2026-10-01 from
`https://www.ietf.org/archive/id/draft-krausz-verification-state-01.txt`) and
`agentoracle-v0.3-2026-05-30.json` (fetched 2026-10-01 from
`https://agentoracle.co/mappings/agentoracle-v0.3-2026-05-30.json`). The
generator and the validator both recompute the recorded digests from these
files; the recorded values are not copied from anywhere else.

## Files

- `mapping.json` — the mapping.
- `mapping.schema.json` — JSON Schema (2020-12) for it; requires every vector to carry a requirement link or a deferral with a reason.
- `generate_mapping.py` — builds `mapping.json` from the manifests at the snapshot commit (`git show`); every count comes from the files, and the mapping judgments and the audit assignments are the tables in this script.
- `validate_mapping.py` — independent checks: manifests read at `corpus_snapshot.commit`, counts and ids, identifiers against the registry, link-or-defer per vector, the reverse view required to EQUAL the forward view scoped to the corpora each view names (both counts for `-01`), digests recomputed from the cited bytes and from the snapshot, the normative audit re-extracted, and the schema (when `jsonschema` is installed). Takes `--mapping PATH`.
- `normative_audit.py` — the sentence extractor shared by the two scripts.
- `negative_controls.py` — three broken copies the validator must reject (an unlinked vector; zeroed `-01` and mapping digests; a wrong snapshot commit) plus the real file it must accept.
- `cited/` — the cited bytes (above).

```
python3 mappings/receipt-verify-registry/generate_mapping.py
python3 mappings/receipt-verify-registry/validate_mapping.py
python3 mappings/receipt-verify-registry/negative_controls.py
```

## What changed in revision 2

1. Reverse view for `-01` reports two counts: all corpora, and excluding `rule2` (NOT NORMATIVE).
2. Finding 1 recorded on `D01-4.1-typ` with the fixtures' actual `typ` values.
3. Omitted `-01` obligations added (§4.1 IANA registry, §9.1 no-mask and terminal-first, §6.1 reject expired, §9.2 unverifiable hash → malformed), cross-referenced; full re-audit of §§3–7, 9, 10 published as `normative_audit`.
4. Every vector linked or explicitly deferred with a reason (schema + validator); `comp-r05`, `comp-r06`, `d1-no-receipt` made explicit deferrals.
5. Validator recomputes the `-01` and mapping-document digests from the cited bytes and reads the corpus at `corpus_snapshot.commit` via `git show`, not the working tree; negative controls added.
