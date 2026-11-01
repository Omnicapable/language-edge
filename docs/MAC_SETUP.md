# Mac compatibility and first test

## Supported installation routes

The pinned PyTorch 2.15 macOS wheel is arm64 with a macOS 14 minimum. Full generation therefore targets Apple Silicon, macOS 14 or later, and native arm64 Python 3.11/3.12. This is a dependency compatibility target, not a claim that hardware testing has been completed.

Intel Macs and older macOS get a viewer-only route using the core numerical/image libraries. They can inspect complete saved maps but cannot generate images or encode imported files with the current generation stack. Rosetta Python on Apple Silicon is rejected for automatic/full installation; install/run native Python instead. An explicit viewer install can use x86 Python.

## Setup

1. Extract the source package and open Terminal in that folder.
2. Run `chmod +x 'Setup Mac.command' 'Start Mac.command'`.
3. Run `./'Setup Mac.command'`. It checks architecture, macOS, Python and memory, then selects the supported install route.
4. Run `./'Start Mac.command'`. Select the bundled demo first.

Use `./'Setup Mac.command' viewer` for explicit viewing only, or `full` to require a compatible generation setup. Existing model packages are not removed by viewer setup. To select a particular Python, set `LANGUAGE_EDGE_PYTHON` to its executable before running setup.

After installation, `language-edge doctor` reports detected platform, memory, packages and GPU availability. MPS checks include one tiny tensor operation. This report is local and is not uploaded by the app.

## Memory and precision

Create a new workspace and choose Automatic or Apple GPU. Standard mode uses float32 generation on Apple GPU. The experimental lower-memory option uses float16 generation on MPS, which can change generated pixels. Record and keep this choice fixed. Image encoding stays float32; the VAE representation method is unchanged. Numerical outputs can still vary by platform or library version.

Generation remains one image at a time. Attention slicing is enabled on MPS. Model references are dropped and the MPS cache is synchronized/released between stages and on normal cleanup/error paths. This releases unused cached memory, not memory still held by another application or active tensor. We do not disable allocator safety limits or silently change devices on failure.

If memory runs out, close other large applications and try a new lower-memory workspace or explicit CPU execution. Do not edit the settings of an already frozen reference. CPU generation can be slow. Encoding precision is deliberately not reduced as an out-of-memory workaround.

## First hardware validation

Start with one SD 1.5 generation and inspect the saved image, then import one image. Next, use the small example prompt set to build a reference, restart the app and reopen it, and generate a query without moving the reference. Observe memory pressure in Activity Monitor and record the chip, RAM, OS and `doctor` output when reporting issues. Avoid sharing private prompts or images in public issue reports.

On an Intel/unsupported Mac, build the complete workspace on a supported GPU machine and copy the folder into the configured data directory for viewing. An external generation service is not integrated in this release.

## References

- [Pinned PyTorch wheel metadata](https://pypi.org/pypi/torch/2.15.0/json)
- [Diffusers MPS guidance](https://huggingface.co/docs/diffusers/optimization/mps)
- [PyTorch MPS backend](https://docs.pytorch.org/docs/2.15/notes/mps.html)
- [MPS cache release](https://docs.pytorch.org/docs/2.15/generated/torch.mps.empty_cache.html)
