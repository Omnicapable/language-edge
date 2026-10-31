# Changelog

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
