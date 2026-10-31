# Third party components

This code uses public APIs and does not redistribute model weights, SAE code, or Terra Obscura source files.

| Component | Project license reported upstream | Source |
|---|---|---|
| PyTorch | BSD-style | https://github.com/pytorch/pytorch/blob/main/LICENSE |
| Diffusers | Apache 2.0 | https://github.com/huggingface/diffusers/blob/main/LICENSE |
| Transformers | Apache 2.0 | https://github.com/huggingface/transformers/blob/main/LICENSE |
| NumPy | BSD 3-Clause | https://github.com/numpy/numpy/blob/main/LICENSE.txt |
| SciPy | BSD 3-Clause | https://github.com/scipy/scipy/blob/main/LICENSE.txt |
| scikit-learn | BSD 3-Clause | https://github.com/scikit-learn/scikit-learn/blob/main/COPYING |
| Pillow | MIT-CMU | https://github.com/python-pillow/Pillow/blob/main/LICENSE |

Installed distributions contain their own license notices, including transitive/native components. Review them when shipping binaries. This repository is source plus installation instructions, not a bundled binary distribution.

SDXL-Turbo's model page reports `sai-nc-community` and directs commercial users to Stability AI's current licensing terms. SD 1.5's model page reports CreativeML Open RAIL-M. These are distinct from the toolkit's code license. Users obtain weights separately and must follow their applicable terms. Model cards checked 30–31 October 2026; recheck before commercial release. No legal clearance is implied.

Terra Obscura provided the workflow background. The original Surkov sdxl-unbox repository has an MIT license, but no source or SAE checkpoint from it is copied into this implementation.
