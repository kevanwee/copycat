# Deterministic scoring v2.0.0

## Shared contract

Scores are technical indices in [0,1], never legal thresholds or the proportion
of infringement. Missing methods return explicit unavailability, not false zero.
Inputs/results are role-bound in the fingerprint. Libraries and video binary
versions are recorded. Round reported metrics to six decimals; use sorted terms
and `math.fsum` for deterministic reductions.

## Text

NFKC Unicode normalization, casefolding, punctuation-to-space and Unicode word
tokens. Apostrophes within words survive. This is lexical processing; no semantic
paraphrase detection, translation or language-specific CJK segmentation. Empty
tokens cause an actionable failure. Maximum 20,000 tokens per document.

| Metric | Method | Weight |
|---|---|---|
| M1 | Set Jaccard of token n-grams; n=min(5, length A, length B) | .35 |
| M2 | Exact LCS/max token length, computed using bit-vector dynamic programming | .25 |
| M3 | Pairwise smoothed TF-IDF cosine on unigrams and bigrams | .30 |
| M4 | Regex named-reference set Jaccard (not a semantic entity recognizer) | .10 |

When both texts have no entity matches, M4 is `null` and the other weights are
renormalized over .90. Absent features do not earn a perfect score. No length
asymmetry discount hides a short excerpt. Report exact-match containment separately.

Evidence uses adaptive up-to-five-token anchors, at most eight original starts
per anchor and fifty extended blocks. Results are ordered by comparison position,
with deterministic longest-match/earliest-position selection. Excerpts show at
most 200 normalized tokens; starts and full block lengths remain. Coverage is
the union of displayed matched intervals on each side, so overlapping windows
cannot inflate it past 100%. It is a lower bound, not exhaustive matching or
legal substantiality. Raw quotations must be checked against source files.

## Images

Apply EXIF orientation; convert to RGB and thumbnail to 1024px bounding box.
Only still images up to 25 million pixels. pHash (.35), per-channel RGB histogram
correlation (.20), grayscale SSIM at 512x512 (.30), ORB good-match ratio (.15).
Identical normalized pixels give a composite of 1. OpenCV uses one thread and
a fixed RNG seed. Flat images may lack keypoints; colour/shape similarity may
be generic. Normalization can discard resolution, alpha and metadata; the
original SHA-256 remains in the report. No automated protected-expression filter.

## Video

FFmpeg normalizes to 2 fps and a padded 640x360 canvas. Compare pHash frame samples
using monotonic alignment, eight-frame lookahead and a .55 candidate threshold.
V1 is average matched hash similarity multiplied by symmetric temporal coverage.
Composite = .75*V1 + .25*aligned SSIM. PSNR/50, clamped to [0,1], is supporting
only. Audio/transcripts are explicitly unassessed (`null`) in the deterministic
workflow. At most 200 aligned timestamps appear in evidence. Reordered scenes,
late clips and heavy edits can be missed; this is not exhaustive video retrieval.

## Reproduction

Fingerprint = SHA-256 of canonical JSON covering full normalized intake, ordered
role/file manifests, similarity outputs, legal nodes/outcome, rulepack content
hash, scoring version, dependency versions and media type. Case IDs and generated
timestamps are excluded. Names are included because they are report provenance.
Rule changes without a version bump still change the rulepack content hash.
Generation time/PDF presentation bytes are not promised byte-for-byte identical.
