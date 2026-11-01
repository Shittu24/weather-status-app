# Evidence log

## October 31, 2026 - city suggestions

- Added debounced city suggestions, populated-place filtering, state/country labels and automatic weather loading by selected GeoNames ID.
- 25 tests pass; lint passes. Verified airport exclusion, selected ID/coordinates, cache reuse, mock suggestions, validation and safe rate-limit responses.
- Rebuilt Docker and verified live Ilorin suggestions distinguish Kwara, Niger and Ondo. Fetching ID 2337639 successfully returned Ilorin, Kwara State weather.
- Browser access host is unavailable; visual and browser interaction verification remains outstanding.

## October 31, 2026 - Open-Meteo integration

- Added live geocoding and current weather, five-minute bounded cache, UTC model valid time, attribution and explicit mock/live modes.
- 22 offline tests pass; lint passes. Tests cover normalization, exact-name preference over landmarks, ambiguity, missing cities, HTTP errors, timeout, cache reuse/expiry and capacity.
- Rebuilt and started Docker with live mode. External smoke checks passed, including a real Atlanta, Georgia lookup returning provider=open-meteo and demo=false.
- Live verification revealed fuzzy geocoding results alongside exact city matches; corrected matching and added regression coverage.
- No browser visual verification performed. Existing TestClient deprecation warning remains non-blocking.

## October 31, 2026 - local foundation

- Implemented the mock provider, API, page, request logs, metrics, Dockerfile and Compose configuration.
- Initial API test run: 14 passed. Covers schema, input, ambiguity, provider timeout/rate-limit/failure sanitization, independent probes, version, page response and bounded telemetry.
- Local test environment resolved Python 3.11.15; Docker targets 3.13.7. Container verification will provide the target-runtime check.
- Initial lint identified import ordering and the intentionally sanitized provider exception boundary; corrected both.
- Final verification: 14 tests passed and Ruff checks passed for app, tests and scripts.
- Docker Compose built and started the Python 3.13.7 image successfully, including a repeat build with the resolved base-image digest pinned in the Dockerfile.
- External HTTP smoke script passed `/health`, `/ready`, `/version` and `/api/weather?city=Atlanta` against the running container.
- `docker compose exec -T weather id` confirmed UID/GID 10001. The app is bound to localhost port 8000.
- Browser automation was unavailable; page content was checked by API tests, but visual layout and browser interaction have not been verified.
- Test dependency warning: Starlette reports that its httpx-based TestClient path is deprecated. Tests still pass; migrate the test transport during a dependency maintenance session.
- Cloud, Kubernetes, CI publishing and GitOps recovery have not been executed. No uptime, latency, cost or recovery claims are made.

For every later experiment record: date, commit, environment, command, expected behavior, observed behavior, cause, fix and verification. Attach evidence only after running the experiment.
