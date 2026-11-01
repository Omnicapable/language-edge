# Security and privacy release review

Reviewed 1 November 2026 for version 0.1.1. This is a source/configuration review, regression testing and dependency advisory snapshot, not a penetration test or a guarantee of safety.

## Decision

Suitable for sharing as an **experimental, single-user local beta**, with the documented platform and measurement limits. Do not expose the Python backend to the internet. A GitHub source repository is the intended distribution channel; it does not host the application backend.

## Findings corrected

1. Legacy tested pins had 110 advisory records across five direct packages at the time of the initial scan. Some concern code paths this tool does not use, but those versions were retired rather than treated as safe defaults. The release now uses current reviewed versions, safe model loading and updated installation tooling.
2. The old packager regenerated its demo from a live workspace. It could have copied later private queries. The audited public archive is now frozen and checksummed; releases never read live runs and use an explicit source allowlist with a credential-pattern gate.
3. Stored imported images could retain metadata. Uploads now validate actual formats/dimensions and produce metadata-free, orientation-corrected PNG copies. This does not anonymize image pixels or source files.
4. Default workspace storage inside a repository could be accidentally shared or synced. New installs use application data outside the repository. Existing folders were not moved or deleted; OneDrive/iCloud and OS backups are outside the app's control.
5. Added cross-origin GET rejection, browser privacy headers, JSON checks, read timeouts and path containment. Existing token/Host checks and restrictive CSP remain in place.

## Verified evidence

- 23 core/security tests passed on Windows, covering request origin/Host boundaries, paths, size/type restrictions, image metadata stripping, release exclusions and the original map invariants.
- Direct pin audit: 11 packages, no known advisories returned.
- Isolated application environment audit: 56 distributions, no known advisories returned; the editable local application itself is not in the advisory database and was reviewed as source.
- Upgraded-stack CPU smoke tests generated and encoded one image with each of SD 1.5 and SDXL-Turbo. Both produced finite 16384-value fingerprints. This is a small functional smoke test, not a new statistical validation.
- Desktop/mobile browser checks passed after the server restart. Browser upload/query checks are recorded separately in the final verification summary.
- Tracked-file and Git-history pattern scans found no credential matches. The initial historical scan inspected 52 blobs; re-run the scanner on the final commit and release. Public demo PNGs had no embedded metadata in the inspection.
- The default-data demo installer was tested on Windows, including packaged-app AppData redirection.

Raw dependency snapshots and smoke results are adjacent JSON files. The credential-pattern scan does not detect every secret or form of personal data, and author identities/planning history were reviewed separately.

## Remaining limits and release steps

- GPU execution on the upgraded stack and Mac hardware execution are not verified. The earlier CUDA pilot used the retired dependency stack. Users need a compatible current PyTorch build and driver; CPU is a slower fallback.
- No 10000-prompt performance run or adequately powered semantic/coverage study has been completed.
- Existing older image files are not retroactively sanitized. Local Word/admin files are excluded from the current public tree; historical planning notes and Git author identities remain in history. No credentials were found that required rotation or history rewriting.
- GitHub publication still needs a chosen destination. Enable private vulnerability reporting, dependency alerts and branch protection as appropriate when creating the repository. CI and Dependabot configuration are present but remote jobs have not run here.
- Recheck advisories before future releases; no scan can promise zero vulnerabilities. Use the local backend only as the current OS user, not as an authenticated multi-user service.

## References consulted

- [PyTorch legacy loading advisory](https://github.com/pytorch/pytorch/security/advisories/GHSA-53q9-r3pm-6pq6)
- [Hugging Face model serialization guidance](https://huggingface.co/docs/hub/security-pickle)
- [Python local HTTP server limitations](https://docs.python.org/3/library/http.server.html)
