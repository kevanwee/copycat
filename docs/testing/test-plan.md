# Test Plan

## Unit Tests
- Text similarity metrics are deterministic and bounded
- Legal rulepack evaluation paths
- Risk band derivation logic

## Integration Tests
- API: create -> upload original/alleged -> analyze -> report
- Celery eager mode analysis completion
- PDF generation endpoint

## E2E Scenarios
- text exact copy
- text low overlap
- video same content re-encode
- video partial clip from original

## Performance Checks
- text within expected latency for typical file sizes
- video 10 min under target on provisioned worker class

## Regression Policy
- Freeze scoring/version constants
- compare rerun outputs for byte-stable key fields