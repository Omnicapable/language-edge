"""Reference-only projection and held-out scoring. No model downloads here."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import os
import re
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps
from scipy.spatial import ConvexHull, QhullError
from sklearn.decomposition import PCA

SCHEMA = 1
MAX_IMAGE_PIXELS = 40_000_000

def default_data_dir():
    """Keep new user data outside a downloaded repository and typical cloud folders."""
    if os.environ.get("LANGUAGE_EDGE_DATA"):
        return Path(os.environ["LANGUAGE_EDGE_DATA"]).expanduser().resolve()
    if sys.platform=="win32":
        return Path(os.environ.get("LOCALAPPDATA",Path.home()/"AppData/Local"))/"LanguageEdge"/"runs"
    if sys.platform=="darwin":
        return Path.home()/"Library/Application Support/LanguageEdge/runs"
    return Path(os.environ.get("XDG_DATA_HOME",Path.home()/".local/share"))/"language-edge/runs"

def clean_image(image):
    """Validate decoded dimensions and strip EXIF, comments and ICC from served copies."""
    if image.width*image.height > MAX_IMAGE_PIXELS:
        raise ValueError("Image is too large; resize below 40 megapixels.")
    if image.format is not None and image.format not in ("PNG", "JPEG", "WEBP"):
        raise ValueError("Choose a real PNG, JPEG or WebP image.")
    rgb = ImageOps.exif_transpose(image).convert("RGB")
    return Image.frombytes("RGB", rgb.size, rgb.tobytes())

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    os.replace(temp, path)

def slug(value):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", value):
        raise ValueError("Use 1–64 letters, numbers, hyphens or underscores for the run name.")
    return value

def unit_vectors(vectors):
    x = np.asarray(vectors, dtype=np.float32)
    if x.ndim != 2 or not np.isfinite(x).all():
        raise ValueError("Expected a finite matrix of fingerprints.")
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    if np.any(norms < 1e-12):
        raise ValueError("A fingerprint is empty or zero.")
    return x / norms

def parse_prompts(text, suffix=".csv"):
    """Deduplicate prompt text; grouping keeps every seed of a prompt in one split."""
    if suffix.lower() == ".jsonl":
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        rows = list(csv.DictReader(io.StringIO(text.lstrip("\ufeff"))))
    result, seen = [], set()
    for row in rows:
        prompt = str(row.get("prompt", "")).strip()
        if not prompt:
            raise ValueError("Every row needs a nonempty prompt column/field.")
        key = " ".join(prompt.casefold().split())
        if key in seen:
            continue
        seen.add(key)
        role = str(row.get("role", "") or "").strip()
        if role and role not in ("reference", "calibration", "evaluation", "query"):
            raise ValueError("Role must be reference, calibration, evaluation or query.")
        result.append({"prompt": prompt, "group": hashlib.sha256(key.encode()).hexdigest(), "role": role})
    if not result:
        raise ValueError("No prompts were found.")
    # Stable split for a given file, with guaranteed calibration in small examples.
    order = sorted(range(len(result)), key=lambda i: result[i]["group"])
    for rank, index in enumerate(order):
        if not result[index]["role"]:
            fraction = rank / len(result)
            result[index]["role"] = "calibration" if fraction < .2 else "evaluation" if fraction < .3 else "reference"
    return result

def nearest(query, reference, k=5, exclude_indices=None):
    """Exact cosine neighbours with bounded temporary distance memory."""
    q, r = unit_vectors(query), unit_vectors(reference)
    k = min(int(k), len(r) - (1 if exclude_indices is not None else 0))
    if k < 1:
        raise ValueError("Not enough reference states for neighbours.")
    all_d, all_i = [], []
    for start in range(0, len(q), 64):
        distances = np.maximum(0, 1 - q[start:start+64] @ r.T)
        if exclude_indices is not None:
            excluded = np.asarray(exclude_indices)[start:start+64]
            valid = excluded >= 0
            distances[np.arange(len(distances))[valid], excluded[valid]] = np.inf
        idx = np.argpartition(distances, k-1, axis=1)[:, :k]
        ds = np.take_along_axis(distances, idx, axis=1)
        order = np.argsort(ds, axis=1)
        all_d.append(np.take_along_axis(ds, order, axis=1))
        all_i.append(np.take_along_axis(idx, order, axis=1))
    return np.concatenate(all_d), np.concatenate(all_i)

def fit_reference(vectors, calibration, k=5):
    x, c = unit_vectors(vectors), unit_vectors(calibration)
    if len(x) < 4 or len(c) < 2:
        raise ValueError("Need at least 4 reference images and 2 held-out calibration images.")
    k = min(k, len(x)-1)
    pca = PCA(n_components=3, svd_solver="randomized", random_state=42)
    coords = pca.fit_transform(x)
    cal_scores = nearest(c, x, k)[0].mean(axis=1)
    return {
        "mean": pca.mean_, "components": pca.components_, "reference": x,
        "calibration_scores": cal_scores, "variance": pca.explained_variance_ratio_,
        "threshold": np.array(float(np.quantile(cal_scores, .99))), "k": np.array(k),
    }, coords

def project(vectors, bundle):
    return (unit_vectors(vectors) - bundle["mean"]) @ bundle["components"].T

def mesh(coords):
    """Convex hull is deliberately an illustration, not a density estimator."""
    try:
        hull = ConvexHull(coords)
        return {"vertices": np.round(coords, 7).tolist(), "faces": hull.simplices.tolist(),
                "method": "3D convex hull of reference points; includes unobserved gaps"}
    except QhullError:
        return {"vertices": [], "faces": [], "method": "Unavailable for a flat or degenerate projection"}

class Run:
    def __init__(self, path):
        self.path = Path(path)
        self.config = read_json(self.path / "config.json")

    @classmethod
    def create(cls, path, config):
        path = Path(path)
        if path.exists():
            raise ValueError("Run already exists. Resume it or choose a different name.")
        path.mkdir(parents=True)
        for folder in ("images", "vectors", "records"):
            (path / folder).mkdir()
        atomic_json(path / "config.json", {"schema": SCHEMA, **config})
        return cls(path)

    def records(self):
        return [read_json(p) for p in sorted((self.path / "records").glob("*.json"))]

    def add(self, image, vector, metadata):
        key = metadata["id"]
        slug(key)
        marker = self.path / "records" / f"{key}.json"
        if marker.exists():
            return False
        vector = np.asarray(vector, dtype=np.float32).ravel()
        unit_vectors(vector[None])
        clean_image(image).save(self.path / "images" / f"{key}.png")
        temp = self.path / "vectors" / f"{key}.tmp"
        with temp.open("wb") as f:
            np.save(f, vector, allow_pickle=False)
        os.replace(temp, self.path / "vectors" / f"{key}.npy")
        atomic_json(marker, {**metadata, "image": f"images/{key}.png", "dimension": len(vector)})
        return True

    def vectors(self, records):
        if not records:
            raise ValueError("No image states are available.")
        return np.stack([np.load(self.path / "vectors" / f"{r['id']}.npy", allow_pickle=False) for r in records])

    def freeze(self):
        if (self.path / "reference.npz").exists():
            raise ValueError("Reference is already frozen. Create a new run to rebuild it.")
        records = self.records()
        plan_path = self.path / "generation_plan.json"
        if plan_path.exists():
            complete = {r["id"] for r in records}
            if any(t["id"] not in complete for t in read_json(plan_path)["tasks"]):
                raise ValueError("Generation is incomplete. Resume it before building the reference.")
        refs = [r for r in records if r["role"] == "reference"]
        cal = [r for r in records if r["role"] == "calibration"]
        groups = [{r["group"] for r in records if r["role"] == role} for role in ("reference", "calibration", "evaluation")]
        if any(groups[a] & groups[b] for a,b in ((0,1),(0,2),(1,2))):
            raise ValueError("Prompt groups leak across reference/calibration/evaluation splits.")
        if len({r["group"] for r in cal}) < 2:
            raise ValueError("Need at least two distinct held-out calibration prompts.")
        bundle, _ = fit_reference(self.vectors(refs), self.vectors(cal))
        bundle["reference_ids"] = np.array([r["id"] for r in refs])
        bundle["calibration_ids"] = np.array([r["id"] for r in cal])
        bundle["config_digest"] = np.array(digest(self.config))
        target = self.path / "reference.npz"
        with (self.path / "reference.tmp").open("wb") as f:
            np.savez_compressed(f, **bundle)
        os.replace(self.path / "reference.tmp", target)
        self.export()

    def export(self):
        target = self.path / "reference.npz"
        if not target.exists():
            raise ValueError("Build the reference first.")
        with np.load(target, allow_pickle=False) as source:
            bundle = {k: source[k] for k in source.files}
        if str(bundle["config_digest"]) != digest(self.config):
            raise ValueError("Configuration changed after freezing the reference.")
        records = self.records()
        vectors = self.vectors(records)
        coords = project(vectors, bundle)
        ref_ids = bundle["reference_ids"].tolist()
        ref_lookup = {key:i for i,key in enumerate(ref_ids)}
        exclusions = [ref_lookup.get(record["id"], -1) for record in records]
        distances, indices = nearest(vectors, bundle["reference"], int(bundle["k"]), exclusions)
        cal = np.sort(bundle["calibration_scores"])
        points = []
        for r,xyz,ds,idx in zip(records, coords, distances, indices):
            score = float(ds.mean())
            points.append({**r, "position": xyz.tolist(), "novelty": score,
                           "calibration_percentile": float(100*np.searchsorted(cal, score, side="right")/len(cal)),
                           "outside": bool(score > float(bundle["threshold"])),
                           "neighbors": [{"id":ref_ids[int(i)],"distance":float(d)} for i,d in zip(idx,ds)]})
        reference_coords = project(bundle["reference"], bundle)
        payload = {"schema": SCHEMA, "name": self.path.name, "model": self.config["model"],
                   "representation": self.config["representation"], "reference_count": len(ref_ids),
                   "calibration_count": len(cal), "threshold": float(bundle["threshold"]), "k":int(bundle["k"]),
                   "variance": bundle["variance"].tolist(), "mesh":mesh(reference_coords), "points":points,
                   "caveat":"Sampled prompt coverage, not a proven language boundary. VAE similarity is experimental.",
                   "calibration_note":"99th percentile of held-out calibration scores; small samples are exploratory."}
        atomic_json(self.path / "map.json", payload)
        return payload
