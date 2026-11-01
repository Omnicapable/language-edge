# Changelog

## 0.1.2 Mac compatibility pass — 1 November 2026

- Added standard-library Mac preflight for native Python, Rosetta, macOS and memory, with auto/full/viewer installation modes.
- Corrected the Intel Mac claim: the pinned PyTorch wheel targets Apple Silicon/macOS 14+, so Intel gets viewer-only rather than a vulnerable dependency downgrade.
- Added a local doctor command and small MPS runtime probe.
- Added explicit device selection and an experimental lower-memory MPS generation option; VAE encoding remains float32.
- Drop models and clean CUDA/MPS caches between stages and on error/cancellation paths. MPS failures preserve completed files and provide actionable recovery guidance.
- Show viewer-only status and disable unavailable generation/import controls when model packages are absent.
- Added simulated Mac regression tests and setup guidance. Actual Mac/MPS hardware execution remains unverified.

## 0.1.1 security and privacy review — 1 November 2026

- Retired vulnerable legacy dependency pins, required current release dependencies, and updated installer tooling. Full fresh-environment advisory scan is recorded in reports.
- Hardened local request origin/Host checks, privacy headers, JSON validation, read timeouts and path containment.
- Validate actual image contents and remove EXIF, GPS, comments and ICC from stored/served copies.
- New UI workspaces default to local application data rather than the repository. Existing workspaces remain untouched and can be reopened explicitly.
- Disable Hugging Face telemetry by default; explain downloads, cloud sync, derived data and sharing risks in PRIVACY.md.
- Freeze and checksum the public demo. Release packaging uses an explicit allowlist, rejects common secret patterns, and never reads live user runs.
- Keep local planning documents/admin helpers out of the current public tree; prior history was scanned rather than rewritten.
- Added targeted security regressions, a security policy, least-privilege CI permissions and Dependabot configuration.
- GPU pilot results remain historical; upgraded-stack verification and outstanding platform limits are recorded separately.

## Monochrome interface update — 31 October 2026

- Changed the interface and coverage mesh to black, white and neutral gray.
- Distinguished point groups with circles, squares, triangles and outlined diamonds, with a ring for selection.
- Renamed the mesh toggle to Coverage envelope. Image previews retain their original colors for inspection.

## 0.1.0 local beta — 31 October 2026

### Implemented

- Independent Python package and CLI with SDXL-Turbo and SD 1.5 adapters.
- Deterministic float32 finished-image VAE posterior means; actual encoder-weight identity checks.
- CSV/JSONL prompts, normalized duplicate removal, grouped splits and seed tracking.
- Incremental images and vector records, two-stage generation/encoding, stop and resume.
- Reference-only PCA, held-out calibration, exact batched cosine neighbours, and frozen reference bundles.
- Import existing images or generate query images without changing the reference.
- Local browser interface with orbit/zoom, clickable points, image previews, neighbours, novelty, PCA variance and optional illustrative convex-hull mesh.
- Local-only serving, request-token/origin checks and bounded uploads.
- Windows/Mac setup launchers, tested dependency constraints, core CI configuration, methods and notices.

### Verification recorded so far

- Seven core tests pass on Windows; dependency consistency check passes.
- SDXL-Turbo: 36 reference-collection generations encoded; fixed map built; four additional generations and one image import added.
- SD 1.5: 12 reference-collection generations encoded; fixed map built; four additional generations and one image import added. Its stop/resume and reference immutability checks also passed.
- Real query cancellation/resume and duplicate prevention passed; reference archive stayed byte-identical.
- Browser automation passed desktop/mobile layout, help, point selection, envelope toggle, camera reset and console checks.
- Browser image upload and query generation/resume completed successfully. The portable precomputed demo was extracted and re-exported with all 41 points.
- Built the wheel and installed it in a fresh environment without PyTorch. Packaged viewer assets were present, all seven core tests passed there, and dependency checks passed.
- Measured VAE sensitivity and 3D information loss are documented in reports. Artistic/semantic validity is not established.

### Pending external verification

- Mac hardware execution and remote CI results.
- 10000-prompt generation/performance and adequately sized calibration.
- Public GitHub destination and publication.

## Planning — 30 October 2026

Created the Word plan and changelog. Recorded the decision to use finished-image VAE encodings, the two-phase workflow, two model targets, and separate maps per representation. The friend's private dataset is not required; development uses an original example prompt collection.
