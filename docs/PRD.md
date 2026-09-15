# Copycat v2 product requirements

## Outcome

Give legal analysts and rights teams a reproducible comparison and a clear
record of the evidence needed for Singapore copyright triage. The product must
never substitute a similarity percentage for a legal finding.

## Delivered workflow

1. Paired text, still-image or visual-video inputs with size/format validation.
2. Explicit category, claim route, conduct date and unknown-by-default legal facts.
3. Evidence explanations for known answers, with a four-factor fair-use worksheet.
4. A case workspace showing missing/contrary limbs, possible exceptions and
   separate technical evidence. Source-linked legal explanations are inspectable.
5. Revision/rerun, PDF/JSON export, session recovery, access-key export and deletion.

## Acceptance requirements

Same substantive inputs, dependencies, versions and outcomes produce the same
fingerprint. Empty extraction fails. Missing media dependencies are explicit.
Private resources require a capability. Mutation invalidates stale results.
Expiry covers all case material. Keyboard/mobile workflows and meaningful
API/scoring/legality regressions are checked in CI.

## Boundaries

Supported legal route: direct infringement of identified authorial work or film
copyright within the reviewed consolidation period. Other routes/categories,
historical facts, underlying film rights and uncertain international protection
need separate analysis. No automatic verdict, fair-use balancing, account-based
tenancy, S3 backend, audio recognition, OCR, semantic paraphrase detection or
cross-medium comparison. Human legal assessments are recorded, not independently
verified. See the [improvement audit](IMPROVEMENT-AUDIT.md) for release evidence.
