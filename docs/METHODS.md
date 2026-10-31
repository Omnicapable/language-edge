# Measurement protocol

## Representation

The first implementation encodes the **finished image**, not an intermediate U-Net layer. The selected model's AutoencoderKL receives EXIF-transposed RGB pixels, center-square cropped and resized with Lanczos to a fixed size. Inputs are mapped to [-1,1]. Encoding uses float32 inference and `latent_dist.mode()` (posterior mean), multiplied by the VAE scaling factor. CHW latents are flattened and L2 normalized. There is no posterior sampling and no SAE. At 512 px the tested models produce 4×64×64 values.

This is a model-associated image representation, not a unique universal location of an image. Different VAEs and preprocessing policies define different spaces. VAE space is optimized for image reconstruction; distances need not reflect conceptual or artistic similarity. Imported images may come from any source but are interpreted by the map's encoder.

## Protocol before evaluating results

- Keep prompt groups and all their seeds in one split. Normalize exact whitespace/case duplicates. Review semantic paraphrases manually.
- Fit PCA on reference vectors only. The held-out calibration vectors determine a 99th-percentile threshold of mean k-neighbour cosine distances. Evaluation vectors assess behavior independently. Calibration is not itself an independent evaluation.
- Default k is 5, reduced for very small references. Every reference score excludes its own vector. Calibration, evaluation and query scores use the same reference and k.
- Freeze the VAE weight hash, preprocessing, reference vectors, PCA, calibration scores, and k. Adding queries cannot update them. Library/device metadata is recorded; byte-identical outputs across hardware or versions are not promised.
- A high score means outside this empirical threshold, not unreachable by language. About 1% flagging on a comparable calibration distribution is expected by construction, not evidence of a discovered language limit.

## Pilot checks and interpretation

Before larger experiments, check deterministic re-encoding, shifted-image and brightness sensitivity, retained PCA variance, and nearest-neighbour agreement between full space and 3D. Compare held-out scores against nested reference subsets. Repeat prompts with different seeds and inspect whether nuisance variation dominates intended similarities. Exact reproducibility and reference immutability are engineering checks. Artistic or semantic validity requires human judgments and a larger designed evaluation.

If an 8 px shift scores comparably to an unrelated image, or full/3D neighbours disagree strongly, surface those limits. Do not automatically switch to an external semantic encoder while still calling it the generator's own latent space. Any alternative representation requires a separately identified map.

## Surface and display

The optional blue mesh is the convex hull of the projected reference states. It contains unobserved gaps and does not encode the kNN decision boundary. The map is a lossy projection; omitted dimensions can make a nearby point have high full-space novelty. All coordinates are display coordinates. Full-space cosine distance and the projected mesh must not be presented as interchangeable.

## References

- [Diffusers AutoencoderKL](https://huggingface.co/docs/diffusers/api/models/autoencoderkl)
- [Latent Diffusion Models paper](https://arxiv.org/abs/2112.10752)
- [scikit-learn PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html)
- [SciPy ConvexHull](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.ConvexHull.html)
- [PyTorch MPS backend](https://docs.pytorch.org/docs/stable/notes/mps.html)
