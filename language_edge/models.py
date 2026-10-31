"""Diffusers adapters. Finished-image VAE means; no SAE or generation hook."""
from __future__ import annotations
import gc
import hashlib
import importlib.metadata
import time
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps
from .core import Run, atomic_json, digest, read_json

PRESETS = {
    "sdxl-turbo": {"source":"stabilityai/sdxl-turbo", "steps":4, "guidance":0.0},
    "sd15": {"source":"stable-diffusion-v1-5/stable-diffusion-v1-5", "steps":20, "guidance":7.5},
}

def device_name(requested="auto"):
    import torch
    if requested != "auto":
        if requested not in ("cpu", "cuda", "mps"):
            raise ValueError("Device must be auto, cpu, cuda, or mps.")
        return requested
    return "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

def weight_identity(vae):
    """Hash actual loaded encoder weights, not just a mutable model name."""
    h = hashlib.sha256()
    for name, value in sorted(vae.state_dict().items()):
        h.update(name.encode())
        h.update(value.detach().float().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()

def new_config(model, source=None, device="auto", size=512):
    if model not in PRESETS:
        raise ValueError("Choose sdxl-turbo or sd15.")
    if size not in (256,512):
        raise ValueError("Encoding size must be 256 or 512.")
    resolved_source=str(Path(source).resolve()) if source and Path(source).exists() else source or PRESETS[model]["source"]
    return {"model":model, "source":resolved_source,
            "device":device, "generation":{"size":512, "steps":PRESETS[model]["steps"],
            "guidance":PRESETS[model]["guidance"]},
            "representation":{"encoder":"vae-posterior-mean", "size":size,
                "preprocess":"exif-transpose RGB center-square Lanczos [-1,1]",
                "vector":"scaled latent CHW flattened then L2 normalized", "metric":"cosine"}}

def load_vae(config):
    import torch
    from diffusers import AutoencoderKL
    source = config["source"]
    local = Path(source).exists()
    kwargs = {"subfolder":"vae", "torch_dtype":torch.float32, "use_safetensors":True}
    if (local and (Path(source)/"vae"/"diffusion_pytorch_model.fp16.safetensors").exists()) or (not local and config["model"]=="sdxl-turbo"):
        kwargs["variant"] = "fp16"
    vae = AutoencoderKL.from_pretrained(source, **kwargs).eval()
    identity = weight_identity(vae)
    expected = config.get("vae_sha256")
    if expected and identity != expected:
        raise ValueError("VAE weights changed. Use the original VAE or create a new reference.")
    dev = device_name(config.get("device", "auto"))
    vae = vae.to(dev)
    vae.enable_slicing()
    return vae, dev, identity

def encode_image(image, vae, device, size):
    import torch
    image = ImageOps.exif_transpose(image).convert("RGB")
    image = ImageOps.fit(image, (size,size), method=Image.Resampling.LANCZOS, centering=(.5,.5))
    data = np.asarray(image, dtype=np.float32).transpose(2,0,1).copy()/127.5-1
    with torch.inference_mode():
        mean = vae.encode(torch.from_numpy(data)[None].to(device)).latent_dist.mode()
        vector = (mean * float(vae.config.scaling_factor)).float().cpu().numpy().ravel()
    if not np.isfinite(vector).all():
        raise ValueError("VAE produced nonfinite values. Try float32 encoding on CPU.")
    return vector

def establish_encoder(run):
    vae, dev, identity = load_vae(run.config)
    if not run.config.get("vae_sha256"):
        if (run.path/"reference.npz").exists():
            raise ValueError("Reference lacks encoder identity; create a new run.")
        run.config["vae_sha256"] = identity
        run.config["versions"] = {m:importlib.metadata.version(m) for m in ("torch","diffusers","numpy","Pillow")}
        atomic_json(run.path/"config.json",run.config)
    return vae,dev

def generate(run, prompts, seeds=(42,), query=False, progress=print, cancel=lambda:False):
    """Save each generation before encoding; both stages resume without repeated work."""
    import torch
    from diffusers import AutoPipelineForText2Image
    if (run.path/"reference.npz").exists() and not query:
        raise ValueError("Reference is frozen. Generate test images with query mode.")
    seeds = [int(seed) for seed in seeds]
    if not seeds or any(seed<0 or seed>2**32-1 for seed in seeds):
        raise ValueError("Supply at least one seed between 0 and 4294967295.")
    staging = run.path/"staging"
    staging.mkdir(exist_ok=True)
    tasks = []
    for prompt in prompts:
        for seed in seeds:
            role = "query" if query else prompt["role"]
            metadata = {"prompt":prompt["prompt"],"group":prompt["group"],"seed":seed,"role":role,
                        "generation":run.config["generation"], "origin":"generated"}
            metadata["id"] = digest(metadata)[:24]
            tasks.append(metadata)
    # An initial run's prompt list is immutable, preventing accidental new calibration/reference data on resume.
    if not query:
        plan = {"tasks":tasks}
        plan_path = run.path/"generation_plan.json"
        if plan_path.exists() and read_json(plan_path) != plan:
            raise ValueError("Reference prompt file or seeds changed. Use the original inputs to resume.")
        atomic_json(plan_path,plan)
    completed = {r["id"] for r in run.records()}
    pending = [m for m in tasks if m["id"] not in completed]
    need_generation = [m for m in pending if not (staging/f"{m['id']}.json").exists()]
    if need_generation:
        dev = device_name(run.config["device"])
        kwargs = {"torch_dtype":torch.float16 if dev=="cuda" else torch.float32, "use_safetensors":True}
        local_source=Path(run.config["source"])
        has_local_half=local_source.exists() and any((local_source/"unet").glob("*.fp16.safetensors"))
        if (dev=="cuda" and not local_source.exists()) or has_local_half:
            kwargs["variant"]="fp16"
        pipe = AutoPipelineForText2Image.from_pretrained(run.config["source"], **kwargs)
        pipe.set_progress_bar_config(disable=True)
        if dev=="cuda":
            pipe.enable_model_cpu_offload()
        else:
            pipe.to(dev)
            pipe.enable_attention_slicing()
        for index,meta in enumerate(need_generation):
            if cancel():
                break
            progress(f"Generating {index+1}/{len(need_generation)}: {meta['prompt'][:70]}")
            settings = meta["generation"]
            started=time.perf_counter()
            with torch.inference_mode():
                result = pipe(meta["prompt"],num_inference_steps=settings["steps"],
                    guidance_scale=settings["guidance"], height=settings["size"], width=settings["size"],
                    generator=torch.Generator(device="cpu").manual_seed(meta["seed"]))
            if getattr(result,"nsfw_content_detected",None) and any(result.nsfw_content_detected):
                raise ValueError("Model filtered a generation. Change the prompt and create a new run.")
            image = result.images[0]
            image.save(staging/f"{meta['id']}.png")
            atomic_json(staging/f"{meta['id']}.json", {**meta,"scheduler":dict(pipe.scheduler.config),
                "pipeline":type(pipe).__name__,"generation_seconds":time.perf_counter()-started})
        del pipe
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    if cancel():
        return
    vae,dev = establish_encoder(run)
    for index,meta in enumerate(pending):
        if cancel():
            break
        progress(f"Encoding {index+1}/{len(pending)}")
        with Image.open(staging/f"{meta['id']}.png") as image:
            vector = encode_image(image,vae,dev,run.config["representation"]["size"])
            run.add(image, vector, read_json(staging/f"{meta['id']}.json"))
    del vae
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    if (run.path/"reference.npz").exists():
        run.export()

def import_images(run, paths, progress=print, cancel=lambda:False):
    if not (run.path/"reference.npz").exists():
        raise ValueError("Build the reference before importing test images.")
    vae,dev = establish_encoder(run)
    for index,path in enumerate(paths):
        if cancel():
            break
        path=Path(path)
        progress(f"Encoding imported image {index+1}/{len(paths)}")
        content_hash=hashlib.sha256(path.read_bytes()).hexdigest()
        with Image.open(path) as image:
            if image.width*image.height>40_000_000:
                raise ValueError("Image is too large; resize below 40 megapixels.")
            vector=encode_image(image,vae,dev,run.config["representation"]["size"])
            run.add(image.convert("RGB"),vector,{"id":"import-"+content_hash[:24],"group":content_hash,
                "role":"query","origin":"imported","prompt":path.name,"seed":None})
    del vae
    run.export()
