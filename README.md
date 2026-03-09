# Copycat

**Singapore-first copyright infringement triage tool** with deterministic similarity scoring for **text, video, and image** works.

> ⚠ Triage only. Not legal advice. Source files are auto-deleted after 24 hours.

---

## Live Deployment

| Service | URL |
|---------|-----|
| Frontend (Vercel) | https://copycat-mu.vercel.app |
| Backend API (Render) | https://copycat-5wgw.onrender.com |
| API Docs (Swagger) | https://copycat-5wgw.onrender.com/docs |

> The Render free tier spins down after inactivity — the first request after a cold start may take ~30 s.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (TypeScript) |
| API | FastAPI + Uvicorn |
| Worker | Celery (eager mode by default; Redis for distributed) |
| Database | SQLite (dev) / PostgreSQL-ready via SQLAlchemy |
| Storage | Local filesystem (dev) / S3-compatible abstraction |
| Reports | ReportLab PDF |

---

## UI Features

| Feature | Details |
|---------|---------|
| **Upload form** | Drag-and-drop / click upload; text, image, and video media types |
| **Live progress** | Polling indicator shows pipeline stage and % completion |
| **Report page** | Similarity score ring, component score bars, legal reasoning flow, evidence passages, PDF download |
| **Footer bar** | Site-wide accreditation bar with copyright notice, Singapore Copyright Act link, and **Terms of Use** modal |
| **Terms of Use modal** | Full Singapore-law-governed ToU (PDPA, warranty disclaimer, liability cap, governing jurisdiction) — opens on click, dismisses on backdrop or button |

---

## Screenshots

**Triage UI — upload form**

![Copycat triage UI](screenshots/ui.png)

**Analysis run — terminal output**

![Test run output](screenshots/runtest.png)

---

## Architecture

### System Overview

```mermaid
graph TD
    subgraph Client["Client Browser"]
        FE["Next.js 14 Frontend\nVercel"]
    end

    subgraph Backend["Backend — Render (Docker)"]
        API["FastAPI\n/api/v1"]
        WORKER["Celery Worker\n(eager / Redis)"]
        DB[("SQLite\nCaseReport · Job · Artifact")]
        FS[("Filesystem\n/tmp/uploads · /tmp/reports")]
    end

    subgraph Pipeline["Analysis Pipeline"]
        EXT["Extraction\ntext · image · video"]
        SIM["Similarity Engine\nM1-M4 · I1-I4 · V1-V4"]
        LEGAL["Legal Engine\nSG Rule Pack v1"]
        PDF["ReportLab\nPDF Renderer"]
    end

    FE -->|"REST (HTTPS)"| API
    API -->|"store artifacts"| FS
    API -->|"write case/job"| DB
    API -->|"enqueue task"| WORKER
    WORKER --> EXT
    EXT --> SIM
    SIM --> LEGAL
    LEGAL --> PDF
    PDF -->|"write report"| FS
    WORKER -->|"update job status"| DB
    FE -->|"poll job status"| API
    FE -->|"fetch report JSON + PDF"| API
    API -->|"read"| DB
    API -->|"read"| FS
```

### Analysis Pipeline

```mermaid
flowchart LR
    UP["Upload\n2 files"] --> CASE["Create Case\n& Artifacts"]
    CASE --> ANALYZE["POST /analyze\nEnqueue Job"]
    ANALYZE --> EXTRACT

    subgraph EXTRACT["1 · Extraction  (10%)"]
        direction TB
        TXT["PDF / DOCX / TXT\n→ raw text"]
        IMG["JPG / PNG / WEBP\n→ 1024px RGB norm"]
        VID["MP4 / MOV / MKV\n→ frames + Whisper"]
    end

    EXTRACT --> SCORE

    subgraph SCORE["2 · Similarity Scoring  (40–55%)"]
        direction TB
        TEXT_SIM["Text  M1 5-gram · M2 LCS\nM3 TF-IDF · M4 NER"]
        IMG_SIM["Image  I1 pHash · I2 Histogram\nI3 SSIM · I4 ORB"]
        VID_SIM["Video  V1 pHash align · V2 SSIM\nV3 PSNR · V4 Transcript"]
    end

    SCORE --> LEGAL

    subgraph LEGAL["3 · Legal Triage  (75%)"]
        direction TB
        SUB["Subsistence\nwork category · originality · SG connection"]
        INF["Infringement\nownership · acts · no authorisation"]
        SUB_TAKE["Substantial Taking\nquality + similarity threshold"]
        EXC["Exceptions\nfair use signal"]
        RISK["Risk Band\nLOW · MEDIUM · HIGH"]
        SUB --> INF --> SUB_TAKE --> EXC --> RISK
    end

    LEGAL --> REPORT

    subgraph REPORT["4 · Report  (90–100%)"]
        JSON["report_json\n(DB)"]
        PDFOUT["PDF\n(filesystem)"]
    end

    REPORT --> DONE["Job: completed\nFrontend navigates\nto report page"]
```

### Data Model

```mermaid
erDiagram
    CASE {
        string id PK
        string jurisdiction
        string status
        json metadata_json
        datetime created_at
    }
    ARTIFACT {
        string id PK
        string case_id FK
        string role "original | alleged"
        string media_type "text | image | video"
        string filename
        string checksum_sha256
        string storage_path
        int size_bytes
    }
    JOB {
        string id PK
        string case_id FK
        string status "queued | running | completed | failed"
        string stage
        float progress
        text error
        datetime updated_at
    }
    SIMILARITY_METRIC {
        string id PK
        string case_id FK
        string metric_code
        float score
        json component_payload
    }
    CASE_REPORT {
        string id PK
        string case_id FK
        json report_json
        datetime generated_at
    }

    CASE ||--o{ ARTIFACT : "has"
    CASE ||--o{ JOB : "has"
    CASE ||--o| CASE_REPORT : "has"
    CASE ||--o{ SIMILARITY_METRIC : "has"
```

---

## Quick start (Docker)

```bash
docker compose up --build
```

- API docs: http://localhost:8000/docs  
- Frontend: http://localhost:3000

---

## Local setup (shell scripts)

```bash
# 1. First-time setup (creates virtualenv, installs deps)
bash setup.sh

# 2a. Start everything at once
bash start.sh

# 2b. Or start services individually
bash start_backend.sh    # FastAPI on :8000
bash start_frontend.sh   # Next.js on :3000
```

> **Windows users:** use Git Bash, WSL2, or the Docker path above.

### Manual setup

```bash
# Backend
cd backend
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Optional video/ML extras:
# pip install -r requirements-video.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate shell)
cd frontend
npm install
npm run dev
```

### Optional Celery worker (distributed mode)

```bash
# Requires Redis running on localhost:6379
cd backend
celery -A app.celery_app.celery_app worker --loglevel=info
```

---

## Similarity Metrics

Copycat produces a **headline overlap percentage** (0–100 %) from a weighted combination of component metrics. All calculations are deterministic: identical inputs always yield identical scores.

### Text Similarity

Four metrics are computed on normalised, tokenised text (punctuation stripped, lowercased):

| ID | Name | Weight | Description |
|----|------|--------|-------------|
| **M1** | 5-gram Jaccard | 35 % | Jaccard similarity of all contiguous 5-token n-grams between the two documents. Highly sensitive to verbatim copying of short phrases. Range [0, 1]. |
| **M2** | LCS Ratio | 25 % | Length of the Longest Common Subsequence (LCS) divided by the length of the longer document (in tokens). Captures structural ordering similarity even when exact phrases are paraphrased. Range [0, 1]. |
| **M3** | TF-IDF Cosine | 30 % | Cosine similarity of TF-IDF weighted unigram+bigram vectors. Downweights common words and amplifies rare shared terms. Range [0, 1]. |
| **M4** | Named Entity Overlap | 10 % | Jaccard overlap of named entities (proper nouns, acronyms, 4-digit years) extracted via regex. Catches identical references to real-world entities. Range [0, 1]. |

**Headline formula:**

```
score = 0.35 × M1 + 0.25 × M2 + 0.30 × M3 + 0.10 × M4
```

The report also returns up to 50 **matched passages** — verbatim 12-token windows that appear in both documents — as evidence snippets.

---

### Video Similarity

Four metrics are computed over sampled frames and optional transcripts:

| ID | Name | Weight | Description |
|----|------|--------|-------------|
| **V1** | Frame pHash Alignment | 50 % | Perceptual hash (pHash) Hamming similarity averaged over monotonically aligned frame pairs, multiplied by temporal coverage. The monotonic alignment uses an 8-frame lookahead and a 0.55 similarity threshold to find matching frame sequences in presentation order. |
| **V2** | SSIM | 20 % | Structural Similarity Index (SSIM) averaged over the same aligned frame pairs. Measures luminance, contrast, and structural differences at the pixel level. Requires `opencv` + `scikit-image` extras. |
| **V3** | PSNR (supporting) | 7 % | Peak Signal-to-Noise Ratio, normalised to [0, 1] by dividing by 50 dB. Penalises pixel-level distortion introduced by encoding rather than genuine content differences. |
| **V4** | Transcript Similarity | 30 % | Full text-similarity pipeline (M1–M4 composite) applied to Whisper-generated transcripts of both videos. Falls back to a visual-only formula when neither video has a transcript. |

**Headline formula (audio present):**

```
score = 0.45 × V1 + 0.18 × V2 + 0.07 × V3 + 0.30 × V4
```

**Fallback (no transcripts):**

```
score = 0.75 × V1 + 0.25 × V2
```

> V2 and V3 are only computed when `opencv-python-headless` and `scikit-image` are installed (`requirements-video.txt`). V4 requires `openai-whisper`.

---

### Image Similarity

Four metrics are computed over normalised (max 1024 × 1024 px, RGB) image pairs:

| ID | Name | Weight | Description |
|----|------|--------|-------------|
| **I1** | Perceptual Hash | 35 % | pHash Hamming similarity — tolerance to minor colour shifts, compression artefacts, and small crops. Fast and robust to minor transformations. |
| **I2** | Colour Histogram | 20 % | Bhattacharyya-coefficient similarity of per-channel (R, G, B) normalised histograms. Detects global colour palette reuse independent of spatial layout. |
| **I3** | SSIM | 30 % | Structural Similarity Index (SSIM), computed on grey-scale thumbnails (256 × 256). Measures luminance, contrast, and structural detail simultaneously. |
| **I4** | ORB Feature Match | 15 % | ORB keypoint descriptor matching (Brute-Force Hamming). Ratio of good matches (< 64 Hamming distance) to the closest 500 keypoints found. Detects local structural reuse even after rescaling or repositioning. |

**Headline formula:**

```
score = 0.35 × I1 + 0.20 × I2 + 0.30 × I3 + 0.15 × I4
```

> I2, I3, and I4 require `Pillow`, `opencv-python-headless`, `scikit-image`, and `imagehash` — all bundled in `requirements-video.txt`. No additional installation is needed if video requirements are already installed.

**Accepted image formats:** JPG/JPEG, PNG, WEBP, GIF, BMP, TIFF/TIF.

---

## Risk Bands

| Band | Headline overlap | Interpretation |
|------|-----------------|----------------|
| **LOW** | < 30 % | Minimal detectable overlap |
| **MEDIUM** | 30 – 70 % | Substantial overlap — further review warranted |
| **HIGH** | > 70 % | High overlap — legal assessment strongly recommended |

Risk band thresholds are defined in the active rule pack (`backend/app/rulepacks/sg_v1.json`).

---

## Determinism Guarantee

Each report is assigned a SHA-256-derived `report_id` computed from:

- `case_id`
- `scoring_version`
- `rule_pack_version`
- sorted SHA-256 checksums of all uploaded artifacts

The same case files, same rule pack, and same software version always produce the **exact same report ID and scores**. This supports reproducibility and audit trails.

---

## Deployment Notes (Render / Docker)

- The `Dockerfile` pins `setuptools<70` via `PIP_CONSTRAINT` to ensure legacy packages such as `openai-whisper` can build their wheels on Python 3.11.
- `COPYCAT_CELERY_TASK_ALWAYS_EAGER=true` (default on Render) runs Celery tasks inline — no Redis required for single-instance deployment.
- PDF generation uses ReportLab Platypus with a styled fallback renderer; if advanced table styling fails (e.g. version skew), a plain-text fallback PDF is produced so the analysis job still completes.
- All uploaded files and reports are written to `/tmp` on Render (ephemeral storage). Set `COPYCAT_STORAGE_ROOT` and `COPYCAT_REPORT_ROOT` to a persistent volume path for production use.

---

## Legal & Compliance

- The analysis output is **triage only** and is **not legal advice**.
- The platform is calibrated to the **Singapore Copyright Act 2021** (No. 22 of 2021).
- A full **Terms of Use** (governing law: Singapore; PDPA-compliant data-handling disclosures) is accessible from the footer of every page.
- Uploaded source files are purged after **24 hours** by default (`COPYCAT_RETENTION_HOURS` env var).
