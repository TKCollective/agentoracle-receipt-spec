# Vector → requirement mapping (receipt-verify registry, methodology §2.7)

`mapping.json` states, for each published conformance vector in this repository
at commit `cbba94b7576cf2aec08c70aeb2899fdfa4d35c66`, which normative
requirement it exercises and whether the corresponding assertion is actually
executed by a published checker (**forward view**), and, for each in-scope
requirement, which vectors exercise it or that none does (**reverse view**).
It is written for the receipt-verify registry's axis §2.7 (*Vector requirement
mapping*, methodology v0.4.5 draft, unchanged from v0.4.1) and follows its
procedure: mapped requirement identifiers resolve in the cited text at the
pinned revision, mapped vectors exist in the corpus, and requirements no vector
exercises are listed.

## Corpora

| Corpus | Manifest | Vectors | Normative | Requirement texts |
|---|---|---|---|---|
| `v0.3-composed` | `examples/v0.3-composed/vectors.json` | 11 | yes | `draft-krausz-verification-state-01`; README "Mycelium Trails" at `196df22b` |
| `v0.4-composed` | `examples/v0.4-composed/vectors.json` | 3 | yes | same |
| `evidence-pinning-rev8` | `fixtures/evidence-pinning-fixtures-v2-rev8.json` | 44 (FINAL) | yes | the evidence-pinning section: review draft + amendments rev5–rev8 at the digests the fixture header pins; rev2 and rev4 at this commit (digests recorded) |
| `rule2` | `conformance/vectors-rule2.json` | 9 | **NOT NORMATIVE** (the manifest's own label) | mapping `agentoracle-v0.3-2026-05-30`; `-01` §5 |
| `leaf-screen-halt` | `examples/conformance/delegation-chain-ref/leaf-screen-halt/vectors.json` | 1 | yes | deferred: its requirement text is third-party (`delegation-chain-ref-v1`) |

Not counted: the 7 vectors on the unmerged v0.4 branch; the rev5–rev7 fixture
files (superseded by rev8).

## Coverage vocabulary

Coverage is recorded only where an assertion is actually executed:

- **covered** — executed by a checker published with the corpus against the shipped file;
- **partial** — declared in the manifest and executed only by the emitter that produced it or by an external run, or the checker exercises part of the requirement;
- **not covered** — no executed assertion.

The reverse view takes the best coverage any vector gives a requirement.
Requirements that live only in third-party texts (`action-ref-v1`,
`delegation-chain-ref-v1`, the Mycelium Provider protocol) are listed under
`external_documents` and never counted as coverage of the in-scope texts.

## Files

- `mapping.json` — the mapping.
- `mapping.schema.json` — JSON Schema (2020-12) for it.
- `generate_mapping.py` — builds `mapping.json` from the manifests at this checkout; every count comes from the files, and the mapping judgments are the tables in this script.
- `validate_mapping.py` — independent checks: counts and ids against the manifests, identifiers against the registry, the reverse view recomputed from the forward view, pinned digests, and the schema (when `jsonschema` is installed).

```
python3 mappings/receipt-verify-registry/generate_mapping.py
python3 mappings/receipt-verify-registry/validate_mapping.py
```
