# Product Requirements Document (PRD) - Copycat v1

## Problem Statement
IP teams need a deterministic, reproducible way to triage copyright infringement risk under Singapore law before escalating to legal counsel.

## Personas
- In-house legal analyst
- Rights management operations staff
- Litigation support analyst

## Goals
1. Determine if copyright can subsist under Singapore triage logic.
2. Produce infringement/substantial-taking risk indicators.
3. Compare original and alleged works with deterministic overlap scoring.
4. Export evidence-backed report in web and PDF formats.

## Non-Goals
- Final legal advice.
- Cross-medium comparison in v1.
- Non-Singapore legal analysis in v1.

## Scope
- Text vs text: txt, pdf, docx
- Video vs video: mp4, mov, mkv, avi

## Functional Requirements
- Case creation with jurisdiction (`SG`).
- Two-artifact upload (`original`, `alleged`) same media type.
- Async analysis job lifecycle.
- Deterministic similarity score + component metrics.
- Singapore legal node-by-node triage output.
- JSON report + PDF export.

## Determinism Requirements
- Fixed preprocessing/tokenization and model/library versions.
- No stochastic decode for transcript extraction.
- Stable score formulas and tie-break rules.
- Report includes `scoring_version` and `rule_pack_version`.

## Retention and Security
- Default retention: 24h for source files/reports.
- Internal use only in v1.
- No external auth in v1.

## Success Metrics
- 100% deterministic reruns for identical inputs.
- >=95% successful job completion for valid files in supported limits.
- Text jobs typically <2 min.
- 10-minute videos typically <8 min at normal queue load.