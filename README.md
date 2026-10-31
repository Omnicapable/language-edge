# Language Edge

An experimental explorer of **sampled prompt coverage in model-specific image VAE representations**. Supply prompts, build a fixed 3D reference map, then import or generate additional images and inspect their positions, neighbours, and novelty.

This project grew out of Terra Obscura. The original demonstration mapped SAE features from generation activations. This implementation instead encodes finished images with the selected model's VAE. Neither an SAE nor access to an image's original generation history is required.

## What the map means

- The real representation is the VAE posterior mean after fixed image preprocessing, flattened and L2 normalized. The default 512 px encoding produces 16,384 values for the supported VAEs.
- PCA is fitted **only on reference images**. Its three coordinates are a lossy view; axes have no intrinsic meaning.
- Novelty is mean cosine distance to the five nearest reference fingerprints, calculated before PCA. Reference points exclude themselves. A held-out calibration set supplies an exploratory 99th-percentile threshold.
- The monochrome wireframe is a **3D convex hull**, not an exact multidimensional boundary. It bridges gaps, including places with no samples. Its inside/outside appearance may disagree with full-space scores.
- VAE distances retain spatial structure; they are **not validated semantic distances**, an impossibility test, or a measure of safety. Small calibration datasets cannot support strong coverage claims.
- Imported images are encoded, not inverted to recover their original noise or diffusion trajectory. Encoding the finished image is not identical to recovering the latent from which it was decoded.

## Installation

Use Python **3.11**, a recent browser, and enough disk space for model weights and outputs. The code supports Python 3.10–3.12. A GPU is recommended for generation; CPU generation can be very slow. Model downloads can require several GB. All processing and serving are local; downloading model files is the only required network activity.

### Windows

Run `Setup Windows.cmd`, then `Start Windows.cmd`. The UI opens at <http://127.0.0.1:8877>.

For an NVIDIA GPU, install a CUDA-enabled PyTorch build in the virtual environment before installing the remaining generation extras. For example, the locally tested CUDA 12.4 build is:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu124
.venv\Scripts\python.exe -m pip install -e ".[generate,test]"
.venv\Scripts\python.exe -m language_edge.cli serve
```

Check your driver and select a compatible build using the [official PyTorch installer](https://pytorch.org/get-started/locally/). The application automatically chooses CUDA when available, otherwise Apple MPS, otherwise CPU.

### macOS

Install Python 3.11. In Terminal, from the project folder:

```bash
chmod +x 'Setup Mac.command' 'Start Mac.command'
./'Setup Mac.command'
./'Start Mac.command'
```

Apple Silicon uses MPS when available, with float32 generation and encoding. This may require substantial unified memory. Intel Macs use CPU. **Mac runtime verification is pending**; launchers and MPS selection are implemented, not hardware-validated. If local generation is impractical, generate a run on a compatible GPU machine and transfer the entire run folder. Inspecting an existing map needs only the core dependencies.

### Viewer only

```bash
python -m pip install -e .
language-edge serve --data runs
```

The UI uses local files only: no CDN, telemetry, or remote frontend dependencies. Leave the server terminal open. It binds only to loopback and is not designed as a shared internet service.

The source release includes `examples/demo-sdxl.zip`. Setup installs it automatically into `runs` if that workspace does not already exist. For a viewer-only installation, run `python scripts/install_demo.py`, then launch the server. The demo has a small calibration set and is for learning the interface.

## Two phase workflow

1. Create a named workspace and choose **SDXL-Turbo** or **Stable Diffusion 1.5**. Optionally select a local Diffusers model folder.
2. Load the example CSV or your own prompt CSV/JSONL. Set comma-separated seeds. Generate reference images. Each image is saved before encoding and completed records survive interruption.
3. Build the 3D map. At least four reference images and two distinct calibration prompts are required; much larger held-out samples are needed for meaningful calibration.
4. Import PNG/JPEG/WebP files, or generate new prompts. The tool applies the saved VAE, preprocessing, PCA and threshold. Adding images never refits the reference.
5. Orbit, zoom, click image points, and inspect nearest examples. Toggle the envelope. Export map metadata as JSON; image files and the frozen reference remain in the run directory.

Use one map per model/representation/configuration. Creating a new reference creates a new workspace. Do not edit the config of a frozen run. The actual loaded VAE weights are hashed and checked before adding new images.

## Prompt formats and splits

CSV:

```csv
prompt,role
A red bowl on a white table,reference
A blue bowl on a white table,reference
A yellow bowl on a white table,calibration
```

Or JSONL:

```json
{"prompt":"A glass chair in a studio","role":"reference"}
{"prompt":"A wooden chair in a studio","role":"calibration"}
```

`role` is optional. The automatic split assigns approximately 70% reference, 20% calibration, and 10% evaluation after sorting normalized prompt hashes. Case/whitespace duplicates are removed, and all seeds for each prompt stay together. Split membership is reproducible for a fixed input file, not guaranteed unchanged when the collection changes. Explicit roles give exact control. Rephrased near duplicates require manual review. The examples above illustrate the format, not sufficient datasets.

Resume with the **same file, roles, seeds and settings**. The reference generation plan is immutable. New prompts belong in query mode or a new workspace. A stop request finishes the current image or encoding operation; model loading and reference construction are not interruptible mid-operation.

## Command line

```bash
language-edge create runs/my-map --model sdxl-turbo
language-edge generate runs/my-map language_edge/web/example.csv --seeds 42
language-edge build runs/my-map
language-edge generate runs/my-map new-prompts.csv --seeds 43 --query
language-edge import-images runs/my-map image1.png image2.jpg
language-edge serve --data runs
```

Use `--model sd15` for SD 1.5. Default generation: 512×512; Turbo uses 4 steps/guidance 0; SD 1.5 uses 20 steps/guidance 7.5. `create --source PATH_OR_HF_ID --device cpu|cuda|mps|auto --size 256|512` supports alternate compatible checkpoints and a smaller encoding size. Generation remains 512×512. Alternate checkpoints are experimental and require a new map and their own license review.

## Data and scaling

Run folders contain config, a generation plan, staged generations, PNG images, per-image `.npy` vectors, atomic JSON completion records, frozen `reference.npz`, and `map.json`. Treat the complete run folder as the portable unit. Do not share private prompts or images unintentionally.

At 512 px, 10,000 float32 VAE fingerprints alone occupy roughly 625 MiB. Images, staging, cached weights and PCA workspaces need additional space. Exact neighbour search is quadratic in reference count and expensive at 10,000 states; it is batched to bound the temporary distance matrix, but this is not a completed 10,000-prompt performance benchmark. Start with 36–100 prompts, measure runtime/storage, then expand. OneDrive synchronization can amplify storage and IO costs.

The initial nearest-neighbour scorer uses cosine on unit-normalized fingerprints. It discards vector magnitude and is sensitive to spatial arrangement. Preprocessing center-crops non-square images; this can remove content. These choices are recorded and must remain fixed within a map.

## Development and status

```bash
python -m pip install -e ".[test]"
python -m pytest -q
python scripts/validate_pilot.py runs/my-map --out reports/my-pilot.json
```

See `reports/` for measured local validation, `docs/METHODS.md` for the protocol, and `CHANGELOG.md` for actual implementation status. No arbitrary model-wide or semantic validity is implied by passing software tests.

## Models and attribution

Weights are downloaded separately, never bundled with this code. Consult the [SDXL-Turbo model card and terms](https://huggingface.co/stabilityai/sdxl-turbo) and the [SD 1.5 model card and terms](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5). Code licensing does not replace model use restrictions. Commercial use requires checking the applicable model terms.

Built with PyTorch, Hugging Face Diffusers and Transformers, NumPy, SciPy, scikit-learn, and Pillow. No SAE code or checkpoint is included. See `THIRD_PARTY_NOTICES.md`.
