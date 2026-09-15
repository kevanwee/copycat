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

Implementation and verification results are recorded below as work completes.
