# Evidence pinning — format text for `draft-krausz-verification-state-02`

**Status: DRAFT for review by @poteshniy and Michael Msebenzi (`headlessoracle`).
Not filed. Not implemented. Text first, deliberately — same loop as the kid-role
increment, which went from draft to frozen in four days because there was text to
read.**

**Base:** filed `draft-krausz-verification-state-01`, sha256
`22c5ce262bdf4e63ef538a308e7a8455e93c4143b9e1726b7b64720615d516db`, 952 lines,
dated 2026-06-12.

---

## 0. The problem this closes, stated plainly

A `verification.*` receipt today pins **the rule** and not **the evidence**.
`v_gate.v_gate_mapping_hash` content-addresses the mapping document, so a verifier
can prove which rule was applied. But the sources are carried as bare URLs. To
recompute a verdict you must re-retrieve them.

That has three consequences, and the third is the one that matters:

1. **Recomputation is not deterministic.** The same URL returns different bytes next
   week. Two honest verifiers can disagree and both be right.
2. **Recomputation depends on a live third party.** If the retrieval provider changes
   or retires, the published reproduction path stops working. This is not
   hypothetical: our own backend provider retires 2026-09-27.
3. **A receipt is therefore a pointer to evidence, not a record of it.** An auditor
   asking in 2029 what was checked in 2026 cannot answer the question from the
   receipt, and neither can we.

The format currently guarantees *which rule was applied* and leaves *what it was
applied to* unpinned. This section closes that.

**Design rule throughout: the evidence block says what was judged. It never says
what the judgment was.** Verdict fields stay exactly where they are.

---

## 1. §2 Terminology — additions

> **evidence item**: A single retrieved source considered during verification,
> identified by its URI and, when pinned, by a cryptographic digest of the
> retrieved content.
>
> **evidence set**: The complete, unordered collection of evidence items
> considered during one verification, together with the metadata that makes it
> recomputable.
>
> **pinned**: An evidence item is pinned when the receipt carries a digest of the
> retrieved content, such that a verifier holding the same content can confirm it
> is the content that was judged. An item carrying a URI alone is **not** pinned.
>
> **offline recomputation**: Re-derivation of a verification outcome from the
> receipt, the referenced mapping document, and the pinned evidence content
> alone, without contacting the issuer or any retrieval provider.

---

## 2. §4.1 JWS Envelope — new `evidence_set` member

**Insert as a new subsection after the existing payload member list:**

> A receipt payload MAY carry an `evidence_set` member describing the sources
> considered during verification. When present it MUST be an object with the
> following members:
>
> | Member | Type | Required | Meaning |
> |---|---|---|---|
> | `evidence_set_version` | string | yes | Version identifier for this block's semantics. This document defines `"ao-evidence-set-v1"`. |
> | `retrieved_at` | RFC 3339 timestamp | yes | When the evidence was retrieved. Distinct from the receipt's issuance time. |
> | `source_count` | integer | yes | Total number of evidence items considered. |
> | `pinned_count` | integer | yes | Number of items carrying a content digest. MUST be less than or equal to `source_count`. |
> | `fully_pinned` | boolean | yes | `true` if and only if `pinned_count` equals `source_count` and `source_count` is greater than zero. |
> | `evidence_root` | string or null | yes | Merkle root over the pinned items per §4.1.2, or `null` when `pinned_count` is zero. |
> | `sources` | array | yes | One entry per evidence item, per §4.1.1. |
>
> `fully_pinned` is stated rather than left to be derived. A reader MUST be able
> to determine that an evidence set is partial without recounting the array, and
> an issuer MUST NOT omit the member when some items are unpinned. **Partial
> pinning is an honest state and is not a defect; concealing it is.**

### 2.1 §4.1.1 — `sources` entries

> Each entry in `sources` MUST be an object with:
>
> | Member | Type | Required | Meaning |
> |---|---|---|---|
> | `url` | string | yes | The URI from which the content was retrieved. |
> | `snippet_sha256` | string or null | yes | Lowercase hex SHA-256 of the retrieved content as received, or `null` if not pinned. |
> | `retrieved_at` | RFC 3339 timestamp | yes | Retrieval time for this item. |
> | `pinnable` | boolean | yes | Whether this item carries a digest. |
>
> `snippet_sha256` is computed over the retrieved content **exactly as received**,
> encoded UTF-8, with no trimming, whitespace collapsing, case folding, or
> Unicode normalization. Any normalization applied before hashing makes the digest
> unreproducible by a third party holding the same bytes, which defeats the
> purpose of carrying it.
>
> An issuer that retrieved content but chooses not to carry the digest MUST set
> `pinnable` to `false` and `snippet_sha256` to `null`. It MUST NOT omit the item:
> **an evidence set that silently drops the sources it cannot pin misrepresents
> what was judged**, which is the failure mode the whole block exists to prevent.

### 2.2 §4.1.2 — `evidence_root` construction

> `evidence_root` is a Merkle root over the pinned items only. Unpinned items
> contribute nothing, because there is nothing about them to commit to.
>
> **Leaf.** For each pinned item, in the canonical order defined below:
>
> ```
> leaf = SHA-256( "ao-evidence-leaf-v1" || 0x00 || url || 0x00 || snippet_sha256 )
> ```
>
> where `url` and `snippet_sha256` are their UTF-8 bytes and `||` is concatenation.
>
> **Interior node.**
>
> ```
> node = SHA-256( "ao-evidence-node-v1" || 0x00 || left || 0x00 || right )
> ```
>
> **Odd node.** When a level has an odd number of entries the final entry is
> **promoted unchanged** to the next level. It MUST NOT be duplicated and paired
> with itself. Duplication admits the well-known second-preimage ambiguity in
> which a tree with a duplicated final leaf and a tree with that leaf genuinely
> present twice produce the same root.
>
> **Canonical order.** Leaves are sorted ascending by `url`, and where two items
> share a `url`, by `snippet_sha256`. Both comparisons are bytewise over the UTF-8
> encoding. Sorting makes the root independent of retrieval rank, so two verifiers
> who retrieved the same evidence in different orders compute the same root.
>
> **Domain separation.** The two distinct prefixes ensure a leaf hash can never be
> reinterpreted as an interior node, and that an evidence root can never collide
> with any other hash tree defined by this document or composed alongside it.
>
> When `pinned_count` is zero, `evidence_root` MUST be `null`. An implementation
> MUST NOT emit a root over an empty set.

---

## 3. §4.3 Verification Protocol — new step

**Insert after the mapping-resolution step, renumbering subsequent steps:**

> N. If the receipt carries an `evidence_set`, resolve it:
>
>    a. Verify `pinned_count` equals the number of `sources` entries whose
>       `pinnable` is `true`, and that `fully_pinned` is consistent with
>       `pinned_count` and `source_count`. An inconsistency is a malformed
>       receipt; gate decision = halt.
>
>    b. If `evidence_root` is non-null, recompute it from the `sources` entries
>       per §4.1.2 and compare. A mismatch is a malformed receipt; gate decision
>       = halt.
>
>    c. If the verifier holds candidate content for a pinned item, compute its
>       SHA-256 and compare with `snippet_sha256`. A mismatch means the verifier
>       does not hold the content that was judged. This is **not** a malformed
>       receipt and MUST NOT halt: it resolves to `unknown` for that item, per the
>       §4.3 halt-rule carve-out.
>
>    d. A receipt carrying no `evidence_set` resolves to `unknown` for this step
>       and MUST NOT fail it. Receipts issued before this section existed remain
>       valid and continue to verify exactly as before.
>
> Steps (a) and (b) are checks on the receipt's **internal consistency** and are
> answerable offline by any verifier. Step (c) is a check against **external
> content** and is answerable only by a verifier that holds it. **Conflating these
> is the error this step is arranged to prevent**: a verifier that cannot obtain
> the content has learned nothing about the receipt's validity, and MUST NOT
> report that absence as a defect in the receipt.

---

## 4. §5 — what an evidence set does NOT establish

**New subsection. This exists because the block will be over-read otherwise.**

> A pinned evidence set establishes that specific content was considered and that
> it has not changed since. It establishes **nothing** about:
>
> - **Truth.** Pinned content can be false. The digest commits to what was judged,
>   never to whether the source was right.
> - **Sufficiency.** A pinned set can be too small, or wrong for the claim. The
>   format does not specify how much evidence is enough.
> - **Independence.** Three pinned sources may be three syndications of one
>   original. See §5.x.
> - **Completeness of retrieval.** The set records what was considered, not what
>   existed. A relevant source never retrieved leaves no trace, and no receipt
>   format can make it do so.
>
> The first and last of these are the ones a reader is most likely to get wrong,
> and an implementation SHOULD NOT present a pinned evidence set to an end user in
> language that implies either.

---

## 5. §5.x — independence, as a declared field only

> An issuer MAY include an `independence` member within `evidence_set`:
>
> | Member | Type | Meaning |
> |---|---|---|
> | `method` | string | Identifier of the method used to compute the measure. |
> | `distinct_registrable_domains` | integer | Count of distinct registrable domains among pinned sources. |
> | `score` | number or null | Implementation-defined measure, or null if not computed. |
>
> **This document does not define how independence is computed, and deliberately
> does not.** Any specific heuristic frozen into a specification becomes
> un-implementable by parties whose corpora differ from the author's, and cannot
> be revised at the speed the problem moves. What is specified is the
> **obligation to declare** the method by identifier, so that two receipts
> carrying independence measures can be compared only when they name the same
> method.
>
> A verifier MUST NOT compare `score` values across differing `method`
> identifiers, and MUST NOT treat the absence of an `independence` member as a
> defect.
>
> *Rationale: source counts are the most commonly inflated figure in verification
> claims — three syndications of one wire story are routinely presented as three
> sources. Naming the method is what makes the number checkable; standardizing the
> method is what would make it brittle.*

---

## 6. Conformance vectors

Proposed path `conformance/vectors-evidence.json`, following the existing
`vectors-rule2.json` convention. Pure logic, no signature material.

| id | designation | input | expect |
|---|---|---|---|
| `evi-root-order-independent` | EVIDENCE / CANONICAL ORDER | same two items, reversed | identical `evidence_root` |
| `evi-root-odd-promotion` | EVIDENCE / ODD NODE | three pinned items | root matches promote-not-duplicate construction |
| `evi-snippet-change-changes-root` | EVIDENCE / BINDING | one snippet byte altered | `evidence_root` differs |
| `evi-partial-pinning-honest` | EVIDENCE / PARTIAL | 2 pinned, 1 unpinned | `fully_pinned` false, `pinned_count` 2, `source_count` 3, resolution not a failure |
| `evi-count-inconsistency-rejects` | EVIDENCE / MALFORMED | `pinned_count` disagrees with `sources` | halt, malformed |
| `evi-root-mismatch-rejects` | EVIDENCE / MALFORMED | root not recomputable from sources | halt, malformed |
| `evi-content-mismatch-unknown` | EVIDENCE / UNKNOWN | verifier holds different bytes | `unknown`, MUST NOT halt, MUST NOT be malformed |
| `evi-absent-unknown` | EVIDENCE / ADDITIVE | no `evidence_set` at all | `unknown`, MUST NOT halt |
| `evi-empty-root-null` | EVIDENCE / EMPTY | zero pinned items | `evidence_root` null, no root emitted |

The last two are the additive-compatibility vectors and are the ones a strict
verifier is most likely to fail.

---

## 7. Three questions for review

Asking these explicitly rather than defending a position, because the answers
change the text.

**Q1 — Should `snippet_sha256` cover the retrieved snippet or the full page?**
Current text says the content as received, which for most providers is a snippet
rather than the full document. A snippet is what was actually judged, which argues
for it. But it is provider-shaped, and two providers returning different snippets
from the same page produce different digests for the same underlying source. Is
that acceptable, or should the format require a full-resource digest where one is
obtainable?

**Q2 — Should `evidence_root` be inside or outside the signed payload?**
Inside is the obvious answer and the current assumption. But an issuer that wants
to publish an evidence set separately from the receipt, or to disclose sources
selectively, would need it addressable independently. Related to the selective-
disclosure work neither of us has scoped yet.

**Q3 — Is `unknown` the right resolution for content mismatch (§3 step c)?**
A verifier holding different bytes for a pinned URL has learned something real:
either the source changed, or the receipt is wrong about what it judged. Current
text resolves `unknown` because the verifier cannot distinguish those two cases.
The alternative is a distinct outcome meaning "pinned content unavailable or
differs," which is more informative but adds a value to a domain we have just
spent two weeks narrowing.

---

## 8. What this does not include, deliberately

- **No anchoring.** A Merkle root over receipts is a separate mechanism and a
  later increment. Anchoring receipts that pin URLs rather than content would
  commit to pointers.
- **No retrieval requirements.** The format does not say how to retrieve, how many
  sources to gather, or which providers are acceptable. That is R21's territory.
- **No changes to any verdict field.** The evidence set describes what was judged.
  Verdict semantics are untouched by this section.
