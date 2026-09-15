# Improvement audit — 15 September 2026

## Scope and acceptance criteria

Build an evidence-led Singapore copyright triage workflow for paired text,
image and video files. Technical similarity must remain separate from legal
findings. Unknown facts remain unknown. Every legal limb needs a pinpoint,
an explained answer, and an actionable evidence gap. Reports must reproduce
the actual inputs and methods. This is a triage product, not a judicial verdict.

## Baseline findings

| Priority | Finding | Required improvement |
|---|---|---|
| Critical | Pipeline assumes originality, ownership, term, qualifying connection and restricted acts; assumes no permission | Typed, explicit fact intake with unknown defaults and supporting notes |
| Critical | Similarity invents access and qualitative substantiality; high-risk path omits causal connection | Evidence-based conjunctive assessment; no numerical legal thresholds |
| Critical | Fair-use checkbox automatically reduces risk | Four-factor review, acknowledgment where relevant, separate statutory exceptions |
| High | RecordTV is assigned another case's neutral citation; generic Act citations and WIPO copy | Verify AGC text and court judgments; version and pinpoint every limb |
| High | Report identity omits facts and artifact roles | Content fingerprint including roles, facts, rulepack contents, results and versions |
| High | Empty/short text earns spurious overlap; quadratic LCS and unbounded match generation | Reject empty extraction; bounded deterministic scoring and traceable passages |
| High | Missing image/video dependencies silently become zero scores | Explicit capabilities and unavailable-method errors |
| High | Public case/job/report access, wildcard CORS, full tracebacks exposed | Case-scoped access secret, origin restriction, safe errors |
| High | Entire upload read before limit; no empty/content validation; files orphan on errors/replacement | Bounded read, validation, safe cleanup and immutable running inputs |
| High | Duplicate jobs, inline eager execution and stale report retrieval | Atomic state transitions, asynchronous local dispatch and revision invalidation |
| High | Retention claim exceeds actual scheduled behavior; derived/report text survives source cleanup | Enforced expiry and deletion covering all case data, honest disclosure |
| High | PDF drops citations and presents confidence percentages as legal certainty | Full reasoning, citations, gaps, provenance and escaped input text |
| Medium | UI collects files only; score ring dominates; legal nodes use internal labels | Guided intake, reviewable facts, prioritized gaps, human-readable legal assessment |
| Medium | No durable case resume, actionable retry, evidence navigation or explicit unknown states | Case workspace with recovery, exports and clear progress/error states |
| Medium | Weak keyboard/mobile/modal behavior; dense evidence output | Accessible labels, focus states, responsive layout and readable excerpts |
| Medium | Dependency posture, deployment instructions and CI need verification | Reproducible installs, backend regressions, frontend build and browser checks |

## Delivery sequence

1. Record audit and verify Singapore legal sources.
2. Implement evidence intake, legal rules and reproducible reports; test and push.
3. Harden scoring, API lifecycle, privacy and retention; test and push.
4. Rebuild intake/report UX and complete integrated verification; push.

## Release boundaries

The system must describe legal answers as supplied assessments. Fair use,
qualitative substantiality, ownership disputes and factual copying require
human judgment. Historical conduct, layered film rights, authorisation and
secondary infringement require explicit routing. Deployment readiness depends
on the tested configuration, persistent storage and operational supervision;
the existence of a live baseline URL is not evidence of production readiness.

## Implemented outcome

All baseline findings above have corresponding implementation changes and
regression coverage or operational documentation on `improve/sg-evidence-triage`.

| Area | Delivered |
|---|---|
| Legal process | Versioned Singapore framework, 13 explicit assessments, supporting bases, four-factor fair-use worksheet, statutory and judgment links, date/category/route scope checks |
| Decision logic | Conjunctive legal limbs; separate unknown, contrary, exception and scope outcomes; similarity never supplies legal facts or a probability of infringement |
| Evidence | Bounded text matching with token positions and coverage, normalized image comparisons, visual video alignment, role-bound hashes and content-derived report identity |
| Case lifecycle | Case access keys, protected previews/exports, bounded uploads, atomic per-case mutations, background analysis, retry, revision invalidation and complete case deletion |
| Privacy | Immediate expiry enforcement, periodic source/derived/report/database cleanup, restricted CORS and no-store responses; backup limitations disclosed |
| UI/UX | Guided three-step intake, explicit unknown answers, legal context help, evidence-first case workspace, prioritized missing facts, editable assessments, PDF/JSON exports and key recovery |
| Accessibility | Responsive mobile layout, keyboard navigation, focus and error states, reduced motion support and automated browser accessibility checks |
| Operations | Non-root containers, health checks, persistent local volume, pinned dependencies, generated OpenAPI, setup/runbook and CI build/startup checks |

## Verification evidence

- Local backend suite: **45 passed**, including text, image and generated-video
  workflows, access isolation, expiry/deletion, content validation, chunked body
  limits, reproducibility and legal branch regressions. The video test used a
  checksum-verified FFmpeg build. CI installs FFmpeg explicitly.
- Browser suite: **3 passed**, exercising the real API, intake, revision,
  protected reports, exports, deletion, mobile/keyboard use and network recovery.
  Automated accessibility checks reported no violations in the tested screens.
- Production frontend build passed. Python unused-name checks, Python formatting
  and frontend formatting are enforced in CI.
- `pip-audit` and `npm audit`: **no known vulnerabilities** at verification time.
- GitHub run [34981983970](https://github.com/kevanwee/copycat/actions/runs/34981983970)
  passed backend, frontend, browser and container build/startup checks for the
  deployment checkpoint. Later commits are subject to the same CI checks.
- Reviewed screenshots: [desktop intake](../screenshots/triage-desktop.png),
  [mobile intake](../screenshots/triage-mobile.png),
  [case report](../screenshots/report-desktop.png).

## Remaining release boundaries

- This is a working triage application with supplied legal assessments. It does
  not independently prove ownership, copying, substantiality or fair use. The
  [legal framework](legal/sg-framework-v2.md) records the reviewed sources and
  gaps in automated source verification. Historical law, foreign qualification
  instruments, other right categories and indirect infringement require review.
- Visual video analysis excludes audio/transcripts. Scanned PDFs need readable
  text supplied separately. Similarity weights are transparent heuristics and
  have not been calibrated as a legal classifier against an adjudicated corpus.
- The supported local deployment uses one API process and local persistent
  storage. Public operation needs HTTPS, external ingress rate/time/resource
  limits, capacity testing, backup policy and operational supervision, as set
  out in the [runbook](ops/runbook.md). It has no account-based team tenancy.
- Accessibility automation does not replace a full assistive-technology audit.
  Tests cover representative workflows, not every browser or hostile file.
- Changes are staged as progressive GitHub commits for review. They do not
  establish that an older hosted baseline has been upgraded or deployed.
