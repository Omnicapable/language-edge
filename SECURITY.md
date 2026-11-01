# Security scope

This is an experimental **single-user local application**, not an internet service. The server binds only to 127.0.0.1. Do not expose it through port forwarding, reverse proxies, tunnels, LAN listeners or public hosting. Publishing the source to GitHub does not host its backend, and GitHub Pages cannot run its Python generation service.

The intended boundary is the local operating-system user. This is not a sandbox for untrusted local software or a multi-user authenticated service. Model libraries and image decoders are native dependencies and need updates.

## Controls

- Strict loopback Host checks, cross-origin request rejection, per-server request tokens for mutations, no CORS allowlist for external sites.
- Same-origin resource policy, no-referrer, no-store, frame denial and a restrictive Content Security Policy.
- Workspace and served-resource path containment checks, with no file-system browsing endpoint.
- JSON request size/type limits and read timeouts. PNG/JPEG/WebP uploads are decoded, bounded by image dimensions and rewritten without metadata.
- SafeTensors model loading and NumPy loading with `allow_pickle=False`. No shell execution, user Python expressions, arbitrary pipeline code or pickle upload endpoints.
- Frozen reference identities and actual VAE weight checks. These protect compatibility, not the trustworthiness of an unknown model publisher.
- Allowlisted releases and an approved, checksummed demo; no auto-publishing or use of private runs to regenerate the demo.

Use only trusted model repositories and checkpoints. Dependency or model vulnerabilities outside a currently used code path can still matter; a clean advisory scan is not proof of safety. Recheck dependencies before each release. Use a current Python 3.11/3.12 patch release and a compatible maintained GPU driver. Do not downgrade packages to the old pilot stack merely to retain driver compatibility.

## Dependency checks

`constraints-tested.txt` records the security-reviewed release versions. GPU tests on the legacy stack are historical evidence, not validation of the new versions. See the dated security review for exactly what was re-tested. Dependency advisory results are a dated snapshot and are not a penetration test or certification.

To audit a fresh environment, install `pip-audit` and run `python -m pip_audit --skip-editable`. Model downloads and advisory checks require network access. The advisory service receives package names/versions, not your workspace images or prompts.

## Reporting

After publishing, enable GitHub private vulnerability reporting and Dependabot alerts/updates. Report security issues privately through the repository Security tab when enabled; do not put tokens, private prompts, images or exploit payloads containing user data in a public issue. If private reporting is not enabled, request a private reporting route without posting sensitive details.

## Known release limits

Mac GPU execution and 10000-prompt workloads have not been verified. The map and novelty metric are experimental and do not establish semantic similarity, image safety or a language frontier. Those are measurement limitations in addition to the software security scope.
