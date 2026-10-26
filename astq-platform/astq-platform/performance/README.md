# Performance baseline (JMeter)

Small, **opt-in** load scenario against the bundled demo shop only.

| Setting | Value |
|---|---|
| Threads | 5 |
| Ramp-up | 5 s |
| Loops | 10 per thread |
| Samplers | `GET /api/products`, `GET /api/products/1` |
| Assertion | HTTP status 200 |
| Target | `DEMO_BASE_URL` (default `http://127.0.0.1:5001`, loopback only) |

## Enable
1. Install Java 11+ and Apache JMeter 5.6.x; put `jmeter` on PATH or set `JMETER_PATH` in `.env`.
2. Enable the suite: `python scripts/set_suite_enabled.py performance_baseline on`
3. Click **Run** on *JMeter Performance Baseline*. ASTQ starts the demo app if needed, runs
   `jmeter -n -t performance/baseline.jmx -l artifacts/runs/<id>/results.jtl -Jhost=… -Jport=…`,
   parses the CSV results (pass/fail samples, average and p95 latency) and shows them on the run page.

> The JMX file is well-formed XML and the result parser is unit-tested against a fixture, but
> JMeter itself was **not installed in the build environment**, so this suite has not been executed
> end-to-end here. Verify it once on your machine before the demo.
