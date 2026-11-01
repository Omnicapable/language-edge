# Implementation audit

Date: 31 October 2026. Project location: the dedicated Language Edge folder.

## Existing assets reviewed

Terra Obscura's caption capture, pilot scorer, final mapper and viewer were reviewed as workflow references. The old pipeline uses SDXL-Turbo, four denoising steps, a Surkov SAE at down.2.1 and pooled 5120D codes at capture step index 3. It uses local paths, a small reference collection, and a display surface that is not a literal high-dimensional boundary.

The new tool does not copy the SAE pipeline or viewer source. Its standalone backend encodes finished images, and its browser canvas viewer has no third-party frontend dependencies. This avoids importing old local paths and assumptions into the public package.

Visual update in 0.1.3: the Dune sky colors and deterministic starfield were subsequently adapted from the user's Terra Obscura viewer. This is a background rendering change only; no SAE capture or scoring code was imported.

## Available environment

- Windows, NVIDIA RTX 4060 laptop GPU with 8 GB VRAM.
- Existing SDXL-Turbo fp16 weights were reused without modifying Terra Obscura.
- The project has an isolated virtual environment that inherits existing model packages for this machine only. Public launchers create an independent virtual environment.
- SD 1.5 model assets are obtained separately from the official community mirror, pinned for the local download to revision `451f4fe16113bff5a5d2269ed5ad43b0592e9a14`.
- Model weights and runs are excluded from Git. No paid service is used.

## Portability and distribution

Source supports Python 3.10–3.12; launchers standardize on Python 3.11. CUDA, MPS and CPU device selection exists. Windows GPU is the available verification platform. Mac GPU execution cannot be validated on this machine. A GitHub Actions matrix is included for future core tests on Windows, Mac and Linux; adding a workflow file does not mean its remote jobs have run.

No GitHub publishing connector or `gh` executable is available in this session. The source repository and release archive can be prepared locally; choosing a destination and pushing a public repository remain external steps.

## Representation review

Finished-image VAE means meet the image import requirement without requiring inversion or generation hooks. Flattened, normalized latents retain spatial arrangement. A small perturbation and seed sensitivity pilot is therefore required and is recorded separately. Software correctness is not semantic or scientific validation.

The illustrative surface is a convex hull, chosen for a small, maintainable first implementation. It deliberately does not implement a density-based edge and must never be described as an exact language frontier.

## Licensing review

Upstream model cards and Diffusers APIs were consulted. SDXL-Turbo and SD 1.5 have separate model terms; the public source does not include weights. A proposed MIT license covers the new toolkit code only. Model permissions, especially commercial use, need the applicable upstream terms. See the third-party notice file for component links. No legal clearance is asserted.
