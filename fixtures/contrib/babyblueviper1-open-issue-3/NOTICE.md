# Contributed vectors: the mixed pinned/unpinned pair (Open Issue 3)

`proposed_vectors_open_issue_3.json` in this directory was written by **babyblueviper1** and is
copied here unmodified from
`babyblueviper1/preaction-governance-conformance`, commit `8e98c0e`,
`examples/evidence-set-cold/proposed_vectors_open_issue_3.json`
(https://github.com/babyblueviper1/preaction-governance-conformance/blob/8e98c0e/examples/evidence-set-cold/proposed_vectors_open_issue_3.json).

**Licence: CC0 1.0 Universal (public-domain dedication).** The author offered the two vectors under
CC0 for inclusion in rev 9 on x402-foundation/tsc issue #4, 2026-09-29
(https://github.com/x402-foundation/tsc/issues/4#issuecomment-5881946061): "They're CC0 if you want
them in rev9." CC0 text: https://creativecommons.org/publicdomain/zero/1.0/legalcode

The rest of that repository is under its own licence (MIT); only these two vectors are covered by
the CC0 statement above. The rest of this repository keeps its own licence.

What the two vectors cover, in the author's stated expected outcomes:

- `evi-duplicate-pinned-unpinned-pair-rejects` — a pinned entry and an unpinned entry sharing `url`
  and `retrieved_at` are one retrieval recorded twice: halt, malformed, `duplicate_bound_tuple`.
- `evi-pinned-unpinned-same-url-distinct-time-accepted` — the same pair with distinct `retrieved_at`
  is two retrievals: accepted, not malformed; the step resolves `unknown` (not fully pinned).

The rev 9 generator reads the inputs, designations and `expect` strings from this file as they are;
it adds the `condition` member the corpus requires on every MALFORMED vector (the value the author's
own `expect` string names) and the attribution members. The file's `checker_result` members record
the author's checker's output and are carried as `contributed_checker_result`; they are his reported
result, not a result of this repository's tooling.
