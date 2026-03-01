# Deterministic Scoring Spec

## Text vs Text
- Normalize: Unicode NFKC, casefold, punctuation strip, whitespace collapse
- Tokenize: deterministic regex tokenization

Metrics:
- `M1`: 5-gram Jaccard
- `M2`: token LCS ratio
- `M3`: TF-IDF cosine (fixed vectorizer settings)
- `M4`: rule-based named-entity overlap

Composite:
`TextScore = 0.35*M1 + 0.25*M2 + 0.30*M3 + 0.10*M4`

## Video vs Video
- Normalize to 2fps and 640x360 padded frame
- Extract frame pHash values
- Monotonic alignment

Metrics:
- `V1`: frame pHash alignment score
- `V2`: SSIM on aligned frames
- `V3`: PSNR diagnostic metric
- `V4`: transcript text similarity (Whisper local, deterministic decode)

Composite:
`VideoScore = 0.50*V1 + 0.20*V2 + 0.30*V4`

## Determinism Controls
- Pinned dependency versions
- Fixed thresholds and weights
- stable sort/tie resolution
- `scoring_version` emitted in report