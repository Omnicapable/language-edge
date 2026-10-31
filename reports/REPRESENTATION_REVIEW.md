# Representation decision after the first pilot

The finished-image VAE route is implemented because it places existing files and new generations using the same model-associated representation without an SAE. The first engineering pilot supports repeatable encoding, not a claim of semantic coverage.

## SDXL Turbo observations

The 36-image reference experiment used 25 reference images, eight calibration images and three evaluation images. Repeated encoding of six images had zero maximum absolute error on the tested CUDA setup. The first three principal components retained about 40.7% of reference variance. Average recall of five full-space neighbours in the 3D nearest-neighbour lists was about 62.2%.

An 8 pixel horizontal shift produced cosine distances of roughly 0.30–0.64, against a median between-reference distance of about 0.68. The shift test uses wraparound and is a nuisance sensitivity diagnostic, not a natural-image benchmark. A 10% brightness change produced distances about 0.008–0.043.

Two same-prompt comparisons across seeds 42 and 43 had cosine distances about 0.64 and 0.73. These are only two pairs, but they underline that prompt identity does not guarantee a compact VAE cluster.

## Decision

Proceed as an **experimental VAE image-space explorer**. Do not promote distances as validated conceptual similarity or the blue mesh as a language limit. Keep the actual score, nearest image examples and PCA variance visible. The reference-size sweep is descriptive and calibration is too small for reliable tail estimates.

Before a research claim or large investment in semantic discovery, evaluate more seeds and image groups using human judgments. If more invariant descriptors are investigated, identify that as a new representation and reference version; do not silently substitute a different encoder or pooling policy.

Raw measurements are in `sdxl-pilot.json` and `sdxl-integration.json`. This document records the interpretation rather than replacing the measurements.
