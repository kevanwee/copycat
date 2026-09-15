# Verification plan — v2

## Backend

- Every necessary legal limb can independently block a supported result.
- Unknown facts, independent creation, permission, incomplete fair use,
  acknowledgment contexts and unsupported scope route correctly.
- Strict intake rejects invented fields and unsupported boolean shortcuts.
- Empty/short/repeated/Unicode text, excerpt containment and exact LCS reference
  comparison protect scoring semantics and resource bounds.
- Real API flows verify PDF/JSON, private routes, revision invalidation, duplicate
  jobs, malformed/oversized files, unreadable PDFs, DOCX tables, image previews,
  replacement cleanup, expiry and deletion.
- Image/video dependencies are installed in CI. Visual video smoke runs against
  synthetic local media when FFmpeg is available; no third-party work is used.

## Frontend

Build and TypeScript checks; real-server Playwright workflow for intake, report,
matches, revision, exports, refresh, access isolation and deletion. Mobile
horizontal overflow, keyboard skip link, input errors and recovery are checked.
Axe checks run on desktop intake/report and mobile intake. Screenshots are
reviewed for layout. These checks are not a complete manual WCAG certification.

## Release

GitHub Actions: Python tests/audit, frontend build/audit, real-server browser
tests, Docker Compose build/start/health. Local environment has no Docker CLI;
container verification therefore runs in CI. New failures or code changes
trigger relevant reruns; passing checks are not repeated without a reason.
