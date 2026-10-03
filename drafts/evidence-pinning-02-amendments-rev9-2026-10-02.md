# Evidence-pinning fixture corpus: rev 9 (2026-10-02)

Rev 9 is a repair of the companion fixture corpus, not a change to the specification. The governing
text is `draft-krausz-verification-state-03` as filed (1 October 2026;
https://www.ietf.org/archive/id/draft-krausz-verification-state-03.txt, sha256
`1d142b3effbfc612dca388567902f63823b45dcf69eece423e6b2b9a28dcbed9`), Sections 5.3 and 5.4.1. Rev 8
stays as published, byte-unchanged.

It exists because of one run. On 2026-09-29 babyblueviper1 reported running his cold-built checker
against the rev 8 corpus (preaction-governance-conformance commit `8e98c0e`,
`run_companion_corpus.py`, harness adaptations H1 to H5 stated in that script's header): 40 of 44
vectors agreed, and the four disagreements were one conflict between the text and the corpus
(x402-foundation/tsc issue #4, https://github.com/x402-foundation/tsc/issues/4#issuecomment-5881946061).
The text stands and the corpus follows it (tsc #4, 2026-09-29,
https://github.com/x402-foundation/tsc/issues/4#issuecomment-5890594710).

## Finding 47 — `snippet_sha256` is present on every entry

-03 Section 5.3.2: "The member MUST be present on every entry." On an unpinned entry it is present
and null. This supersedes rev 6 Finding 30's omission-equivalence **for this member only**; the
absent-or-null rule for `content_kind` on an unpinned entry is unchanged.

Four positive fixtures omitted the member on an unpinned entry and expected acceptance. They are
regenerated with an explicit `"snippet_sha256": null` on that entry and are otherwise unchanged:

- `evi-fully-pinned-fallback-derives-from-sources-accepted`
- `evi-root-present-pinned-count-absent-accepted`
- `evi-unpinned-item-reason-content-not-held`
- `evi-unpinned-members-absent-accepted` — this vector existed for the absent limb of rev 6
  Finding 30. With `snippet_sha256` now explicit, it exercises that limb for `content_kind` only,
  and its `expect` string says so.

## Finding 48 — the omission has a named condition and a vector

-03 Section 5.3.2 names the omission on an unpinned entry `snippet_sha256_member_absent`. New
vector `evi-snippet-sha256-member-absent-on-unpinned-rejects` (MALFORMED): an unpinned entry with a
valid `unpinned_reason` and no `snippet_sha256` member.

## Finding 49 — condition identifiers follow the -03 registry

Eight identifiers the rev 8 corpus carried predate the registry in -03 (the condition table in
Section 5.4.1). They are renamed, and the old values are published as superseded
(`header.superseded_conditions`) so a rev 8 run can be compared with a rev 9 run:

| rev 8 identifier | rev 9 identifier (-03 registry) |
|---|---|
| `content_kind_absent_when_pinned` | `content_kind_absent_or_invalid_when_pinned` |
| `pinned_count_disagrees_with_pinned_entries` | `pinned_count_mismatch` |
| `root_null_with_pinned_entries` | `evidence_root_absent_with_pinned_items` |
| `root_present_with_zero_pinned` | `evidence_root_present_with_no_pinned_items` |
| `snippet_digest_present_for_full_resource` | `resource_sha256_present_for_full_resource` |
| `source_count_disagrees_with_sources` | `source_count_mismatch` |
| `unpinned_reason_outside_domain` | `unpinned_reason_absent_or_invalid` |
| `unpinned_without_reason` | `unpinned_reason_absent_or_invalid` |

These are the same eight renames babyblueviper1's H5 adaptation applied to the rev 8 names; under
rev 9 that mapping has nothing left to rename. Nine vectors carry one of these identifiers; their
inputs, designations and `expect` strings are unchanged, except
`evi-full-resource-digest-on-unpinned-rejects`, which also carries the explicit null of Finding 51.

## Finding 50 — the mixed pinned/unpinned pair has vectors

The rev 8 README recorded that no vector covered a pinned entry and an unpinned entry sharing `url`
and `retrieved_at` (rev 8 Finding 35's stated consequence; -03 Section 5.3.2: "A pinned entry and an
unpinned entry sharing url and retrieved_at are, by the same rule, one retrieval recorded twice.").
Two vectors contributed by babyblueviper1 under CC0 close it, with his stated expected outcomes:
`evi-duplicate-pinned-unpinned-pair-rejects` (halt, `duplicate_bound_tuple`) and
`evi-pinned-unpinned-same-url-distinct-time-accepted` (accepted; step resolves `unknown`). See
`fixtures/contrib/babyblueviper1-open-issue-3/NOTICE.md`.

## Finding 51 — one MALFORMED vector gets the explicit null too

`evi-full-resource-digest-on-unpinned-rejects` (MALFORMED, `resource_sha256_present_for_full_resource`)
carried an unpinned entry that omitted `snippet_sha256`, as in rev 8. Under -03 Section 5.3.2 that
omission is itself malformed, so a checker that reports every condition listed
`snippet_sha256_member_absent` beside the condition the vector exists for. The entry now carries an
explicit `"snippet_sha256": null`; nothing else in the vector changed apart from the Finding 49
rename. After this, the only vector in the corpus that omits the member on an unpinned entry is the
one that exists to omit it (Finding 48); the generator and the cross-check both fail the build
otherwise.

What this does not achieve, stated so it is not assumed: the vector still breaks two rules under
-03, not one. Its purpose is the full-resource rule applied to an unpinned entry, which requires
`content_kind: full_resource` on that entry, and -03 Section 5.3.2 names a non-null `content_kind`
on an unpinned entry `content_kind_present_when_unpinned`. A checker that reports every condition
lists that alongside `resource_sha256_present_for_full_resource`. The vector's named condition and
its expected outcome (halt) are unchanged. Decided 2026-10-02 after the first rev 9 cut was reviewed
and before rev 9 was published.

## What rev 9 does not do

- It changes no other vector. Thirty-one of the forty-four rev 8 vectors are byte-identical in the
  emitted set, eight differ only in their `condition` identifier, and five differ in the input: four
  as described under Finding 47, and one under Finding 51 (that one also carries a Finding 49 rename).
- It does not add vectors for the -03 registry conditions that are not named as a vector's
  condition in this corpus (`content_kind_present_when_unpinned` is triggered by one vector, see
  Finding 51, but named by none):
  `evidence_set_not_object`, `evidence_set_version_absent_or_not_string`,
  `evidence_set_version_unsupported`, `fully_pinned_mismatch`, `sources_not_array`,
  `source_entry_not_object`, `url_absent_or_not_string`, `snippet_sha256_present_when_unpinned`,
  `snippet_sha256_not_lowercase_hex64`, `content_kind_present_when_unpinned`,
  `resource_sha256_not_lowercase_hex64`, `member_contains_nul`.
- The vectors remain fragments (bare `entry` / `sources` shapes, no `evidence_set_version`, roots
  omitted where a vector is not about the root), exactly as in rev 8, so the H1 to H5 harness
  adaptations of the rev 8 run apply unchanged. The two contributed vectors are complete
  `evidence_set` objects, as their author wrote them.
- **No implementer has run rev 9.** A result against it is reported only when its author reports it.
