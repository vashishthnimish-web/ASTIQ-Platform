# ASTQ REST API Specification (v1.0)

Base URL (local): `http://127.0.0.1:5000`. All API responses are `application/json`.
API routes are **exempt from browser CSRF** (they use no cookies); if the app is ever exposed beyond
localhost, add token authentication first (see Known Limitations).

## Error format
```json
{"error": {"code": "SUITE_NOT_FOUND", "message": "No registered suite with key 'ghost'"}}
```
| HTTP | Used for | Codes |
|---|---|---|
| 400 | malformed / invalid input | `INVALID_REQUEST`, `INVALID_SUITE_KEY`, `BAD_REQUEST` |
| 404 | unknown route/resource | `SUITE_NOT_FOUND`, `RUN_NOT_FOUND`, `NOT_FOUND` |
| 405 | wrong method | `METHOD_NOT_ALLOWED` |
| 409 | state conflict | `SUITE_DISABLED` |
| 500 | unexpected failure | `INTERNAL_ERROR` |

## Endpoints

### GET /api/health
`200` → `{"status":"ok","service":"astq"}`

### GET /api/suites
`200` → `{"suites":[{"suite_key":"api_smoke","name":"Demo Shop API Smoke","description":"…","type":"API","enabled":true}, …]}`
The server-side command is never exposed.

### GET /api/suites/{suite_key}
`200` suite object · `404 SUITE_NOT_FOUND`

### POST /api/runs
Body: `{"suite_key":"api_smoke"}` (`suite_key`: 1–64 chars of `a-z 0-9 _`)
`202` → `{"run_id":7,"status":"QUEUED","suite_key":"api_smoke","links":{"self":"/api/runs/7"}}`
Errors: `400 INVALID_REQUEST` (no JSON / no key), `400 INVALID_SUITE_KEY`, `404 SUITE_NOT_FOUND`, `409 SUITE_DISABLED`.
Execution happens in a background worker; poll the run URL.

### GET /api/runs
Query: `suite_key`, `status` (QUEUED|RUNNING|PASSED|FAILED|ERROR|CANCELLED, case-insensitive), `page` (default 1), `per_page` (1–100, default 20).
`200` → `{"runs":[…],"page":1,"per_page":20,"total":4,"pages":1}` newest first. `400` for an unknown status.

### GET /api/runs/{run_id}
```json
{
  "id": 3, "suite_key": "sample_mixed", "suite_name": "Sample Mixed Results (intentional failure)",
  "status": "FAILED",
  "created_at": "2026-10-19T08:26:49Z", "started_at": "…", "finished_at": "…",
  "duration_seconds": 0.8, "return_code": 1,
  "counts": {"passed": 2, "failed": 1, "error": 0, "skipped": 1},
  "summary": "4 tests: 2 passed, 1 failed, 0 errors, 1 skipped",
  "error_kind": null,
  "artifacts": {"console": "/runs/3/artifacts/console.log", "junit": "/runs/3/artifacts/junit.xml", "report": "/runs/3/artifacts/report.html"}
}
```
`404 RUN_NOT_FOUND`. `counts` values are `null` when results could not be parsed.

## Status & error semantics
| Status | Meaning |
|---|---|
| QUEUED / RUNNING | persisted before / during execution |
| PASSED | parsed results, no failed/errored tests, exit code 0, ≥1 test passed |
| FAILED | at least one test failed or errored |
| ERROR | runner problem — `error_kind`: `TIMEOUT`, `SPAWN_ERROR`, `PARSE_ERROR`, `NONZERO_EXIT`, `NO_TESTS_EXECUTED`, `TARGET_NOT_AUTHORIZED`, `INTERRUPTED`, `INTERNAL_ERROR` |

## Browser pages
`/` dashboard · `/suites` · `POST /suites/{key}/run` (CSRF) · `/runs` (`?suite=&status=&page=`) · `/runs/{id}` · `/runs/{id}/artifacts/{console.log|error.log|junit.xml|report.html|results.jtl}`
