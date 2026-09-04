# Evidence pinning — amendments rev 3 for `draft-krausz-verification-state-02`

**Status: DRAFT amendments for review. Not filed. Not implemented.**

**Replaces** `evidence-pinning-02-amendments-rev2-2026-09-04.md` (sha256
`a957802a4ed4d5a4097e2066fd0be4cbc5bf5d777ebbd5809e47f3bd4637bf74`), which stays on disk
byte-unchanged. One change from rev 2: **§4.1.1's possession clause is rewritten to attach
the obligation at receipt rather than at retention.** Nothing else in rev 2 is affected;
every other finding, ledger entry, vector, and §8 citation stands as filed.

**Base:** `drafts/evidence-pinning-02-review-draft.md`, sha256
`9832156998ceb35f25d08c5be2d4d7c314477b25045f4499e07f3c5e501f5096`.

## Provenance of this change

Rev 2 §4.1.1 stated:

> An issuer MUST pin every evidence item for which it received content bytes. `pinned` MAY be
> `false` **only** where no content bytes were received **or retained** for that item.

with `content_not_retained` in the enumerated domain of `unpinned_reason`, defined as
"content bytes arrived and were discarded before a digest was computed."

Raised as an open question to `headlessoracle` 2026-09-04 in the file
`possession_rule_retention_loophole_2026-09-04.md`: the disjunction "received or retained"
placed a fact the issuer does not control ("received") beside a choice the issuer does
("retained"), and `content_not_retained` was the enumerated form of the choice. Under that
wording an issuer could receive the contradicting source, judge it, decline to hash it,
declare `content_not_retained`, and conform — which is the selective-pinning move §4.1.1
was written to remove. Held back from the message deliberately: the observation that a
digest can be computed at receipt and survives discarding the content, so
`content_not_retained` explains an inability to *reproduce content later* (already covered
by §5) but never an inability to *pin*.

`headlessoracle` reply, same day:

> On 4.1.1 you are right, and the error is mine. "Received or retained" put a fact the
> issuer does not control beside a choice it does, and `content_not_retained` names the
> choice. An issuer that received the contradicting source, judged it and declined to hash
> it could sign `content_not_retained` and be conformant, which is the selective-pinning
> move I said the rule removed. The obligation attaches at receipt. Retention has nothing
> to do with pinning: a digest needs the bytes only while they are held, a pipeline that
> judged bytes had them at the moment of judgement, and hashing is cheaper than judging.

He also supplied a clarifier this file had not written and needs, closing the streaming
edge case that would otherwise reopen the loophole. His words are seated verbatim in the
replacement clause below.

Two reviewers, two mechanisms for the same gap, arriving at the same collapse: the
observation about digest-at-receipt was reached independently on both sides. This is the
third round of that pattern with the same reviewer and the second where it landed inside
normative text.

## The replacement clause — full §4.1.1 text

Replaces the entire rev 2 §4.1.1 quoted block. Comparison with §4.1.2, §5, and §6 shows no
downstream language depends on `content_not_retained` as a permitted value; the enumerated
domain shrinks from three values to two, and the "false statement" paragraph applies to the
two-value domain unchanged.

> An issuer MUST pin every evidence item for which it received content bytes. `pinned` MAY be
> `false` **only** where no content bytes were received for that item.
>
> The digest is computed over the content bytes **as received**, before or alongside any
> judgement. Whether the bytes are kept afterwards is irrelevant to pinning; the digest is
> the only thing the format asks an issuer to keep.
>
> Every item with `pinned: false` MUST carry an `unpinned_reason` from this domain:
>
> | Value | Meaning |
> |---|---|
> | `no_content_returned` | The retrieval attempt returned no content bytes. Covers refusal, paywall interception, robots exclusion, and transport failure alike — the receipt records that nothing arrived, not why. |
> | `provider_metadata_only` | The retrieval surface returned metadata about a resource without its content. |
>
> An item with `pinned: false` and no `unpinned_reason`, or with a value outside this domain,
> is a malformed receipt; gate decision = halt.
>
> An issuer that received content bytes for an item and declares either value has signed a
> false statement. **The format cannot verify possession from the receipt.** What it does is
> convert selective pinning from a permitted state into a lie — the same status as any other
> false statement a signed receipt could carry, and subject to the same consequences outside
> the format.

**Why possession and not composition.** (Unchanged from rev 2; retained verbatim.) A
composition rule — pin every source that refutes the verdict — cannot be written, because
"refutes" is the issuer's own classification and an issuer wanting to conceal a source
classifies it as irrelevant. Policing that requires a third party to re-retrieve and
re-evaluate the evidence, which is the live dependency this whole section exists to remove.
Possession is different in kind: **whether bytes arrived is a fact about the issuer's own
process, not a judgment about a source.** It can therefore be stated normatively without
requiring anyone to check anything, and its falsification is a lie rather than a defensible
reading.

## What this closes and what it does not

**Closes:** the receive-judge-declare-not-retained walk. A digest was computable at receipt;
declining to compute it is now a lie whether the bytes are still held or not. The streaming
case is closed by the second sentence: a pipeline that reads bytes into a decoder,
tokenizer, or judgement pass had them at some moment, and that moment is the moment at
which pinning is due.

**Does not close:** an issuer that never receives the bytes. That case is what
`no_content_returned` records, and it remains legitimately unpinnable; the receipt cannot
distinguish "server declined" from "issuer chose not to request." Both collapse to the same
declared state, which is the honest limit stated in §5.

**Does not require:** any bytes to be retained beyond the digest. The retention envelope
under §5 is unchanged. What the format asks an issuer to keep is 32 bytes per pinned item,
not the source content.

## Diff against rev 2, in words

| Element | Rev 2 | Rev 3 |
|---|---|---|
| First sentence tail | "received or retained" | "received" |
| Second sentence | (none) | Digest-at-receipt clarifier, from Beenz's reply verbatim |
| `unpinned_reason` domain | 3 values (adds `content_not_retained`) | 2 values (`no_content_returned`, `provider_metadata_only`) |
| "false statement" paragraph | applies to three values | applies to two values; word count adjusted |
| "Why possession and not composition" | verbatim | verbatim, unchanged |

## Downstream consistency checks

**§4.3 step (a)** — the gate decision on unpinned items still reads *"every entry with
`pinned: false` carries an `unpinned_reason` from the §4.1.1 domain."* Domain-membership
check remains correct; the domain has one fewer permitted value.

**§6 vector table** — `evi-unpinned-reason-outside-domain-rejects` now rejects
`content_not_retained` (previously accepted). No new vector is required; the existing
vector's semantics tighten with the domain. **`evi-unpinned-without-reason-rejects`** is
unaffected.

**§5 limits section** — bullet 3 ("not the time," retrieval-timing understatement) still
applies. The digest-at-receipt clarifier does not overclaim: it says nothing about when
retrieval happened, only that pinning is due at that moment.

**§8 citation** — unchanged. `@headlessoracle/receipt-verify@0.1.2` by version, integrity,
and tag; annotated-tag precision preserved.

## Findings ledger — one entry amended, all others stand

| # | Finding | Disposition |
|---|---|---|
| 6 | Possession rule: pin what you received; mandatory `unpinned_reason` | **Amended in rev 3** — obligation attaches at receipt, not at retention. `content_not_retained` removed from the domain. Reviewer supplied the digest-at-receipt clarifier. |

Findings 1–5 and 7–14 stand as filed in rev 2. Both rev 2 reversals (unpinned_reason
required, `offline_recompute` member dropped) also stand.

## Open questions from rev 2 — status

- **Q-a — `content_kind` required only when pinned?** Unchanged; still open.
- **Q-b — fourth possession value?** **Closed by this revision.** With the retention branch
  removed, the domain has two values and neither review has produced a candidate for a
  third. If one appears later it is additive.
- **Q-c — `evidence_set_version` bump for detached-sources increment?** Unchanged; still open.

## Status of the file for review

Rev 2 remains on disk under its own filename, unchanged. Rev 3 is this file. Per
`semantics_change_new_filename.md` (filed today): the rev 2 → rev 3 change is a normative
narrowing — a permitted state becomes malformed — which is a semantics change and takes a
new filename. The two are separately citable; a reader holding rev 2 gets rev 2's rule, a
reader holding rev 3 gets the tightened one.
