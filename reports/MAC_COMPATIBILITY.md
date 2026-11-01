# Mac compatibility pass

Date: 1 November 2026. Release: 0.1.2.

## Implemented

- Standard-library installation preflight checks macOS, native Python architecture, Rosetta and unified memory before model packages are installed.
- Auto/full/viewer setup modes. The pinned torch 2.15 wheel is macosx_14_0_arm64; full generation targets Apple Silicon/macOS 14+. Intel and older systems have a viewer-only route without insecure downgrades.
- Runtime doctor checks model-package availability and probes one tiny MPS operation when supported.
- Explicit device choice and opt-in lower-memory MPS generation. Standard MPS generation remains float32; lower-memory MPS generation uses float16. Finished-image VAE encoding stays float32 in both modes.
- Model references and unused CUDA/MPS caches are cleaned between stages, cancellation and failure paths. Errors preserve completed files and explain explicit CPU/lower-memory recovery rather than silently changing the reference settings.
- Viewer-only UI disables operations that require absent model packages and explains the limitation.

## Checks performed here

33 core, security and compatibility tests passed on Windows. Mac tests simulate native ARM, Rosetta, Intel, older macOS, precision policy, MPS cache release and error handling. They do not execute on a Mac GPU.

A real Windows CPU regression generated and encoded one SDXL-Turbo image through the refactored pipeline, producing 16384 finite values. CPU generation remained float32 even when the lower-memory profile was selected. The numerical representation method was unchanged. See `mac-compatibility-checks.json`.

Desktop/mobile browser checks passed, including new device/memory controls, map selection, image upload and query completion. Git Bash parsed the Mac launchers for syntax; this is not a Finder/Terminal or package installation test on macOS. Dependency consistency passed. No new dependencies were added to the reviewed 0.1.1 pin set.

## Still required on real hardware

Run setup and doctor, generate one image in Standard and lower-memory modes, import an image, build a small map, restart and reopen it, then add a query. Check memory pressure and cancelled/error recovery. Validate image quality and numerical behavior before using the experimental precision option for a large reference collection.

Full generation is not advertised for Intel Macs. Existing saved maps can be viewed there. Current-stack NVIDIA GPU and 10000-prompt performance also remain outside this verification.

## Sources

- [PyTorch 2.15 wheel metadata](https://pypi.org/pypi/torch/2.15.0/json)
- [Diffusers MPS guidance](https://huggingface.co/docs/diffusers/optimization/mps)
- [PyTorch MPS cache behavior](https://docs.pytorch.org/docs/2.15/generated/torch.mps.empty_cache.html)
