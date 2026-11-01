"""Local-only browser UI with one serialized worker and no external assets."""
from __future__ import annotations
import base64
import io
import importlib.util
import json
import mimetypes
import secrets
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote
from .core import Run, atomic_json, parse_prompts, read_json, slug, clean_image, default_data_dir
from .models import PRESETS, new_config
from PIL import Image

class Jobs:
    def __init__(self):
        self.lock=threading.Lock()
        self.state={"status":"idle","message":"Ready"}
        self.stop=threading.Event()

    def start(self, name, operation):
        with self.lock:
            if self.state["status"]=="running":
                raise ValueError("A task is already running. Wait or stop it before starting another.")
            self.stop.clear()
            job_id=time.time_ns()
            self.state={"id":job_id,"status":"running","message":name}
        def progress(message):
            self.state={"id":job_id,"status":"running","message":message}
        def worker():
            try:
                operation(progress,self.stop.is_set)
                self.state={"id":job_id,"status":"stopped" if self.stop.is_set() else "complete",
                    "message":"Stopped. Resume with the same inputs." if self.stop.is_set() else "Task complete"}
            except Exception as exc:
                traceback.print_exc()
                self.state={"id":job_id,"status":"error","message":f"{type(exc).__name__}: {exc}"}
        threading.Thread(target=worker,daemon=True).start()

def handler_class(data, jobs):
    data=Path(data).resolve()
    static=Path(__file__).parent/"web"
    token=secrets.token_urlsafe(32)
    models_installed=all(importlib.util.find_spec(m) for m in ('torch','diffusers','transformers','accelerate'))
    class Handler(BaseHTTPRequestHandler):
        server_version="LanguageEdge"
        sys_version=""

        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def log_message(self,fmt,*args):
            pass

        def send(self,status,body,kind="application/json"):
            if not isinstance(body,bytes):
                body=json.dumps(body,ensure_ascii=False).encode() if kind=="application/json" else body.encode()
            self.send_response(status)
            self.send_header("Content-Type",kind)
            self.send_header("Content-Length",str(len(body)))
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Referrer-Policy","no-referrer")
            self.send_header("Cross-Origin-Resource-Policy","same-origin")
            self.send_header("X-Frame-Options","DENY")
            self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers(); self.wfile.write(body)

        def trusted_host(self):
            return self.headers.get("Host") in (f"127.0.0.1:{self.server.server_port}",f"localhost:{self.server.server_port}")

        def run_path(self,name):
            folder=(data/slug(name)).resolve()
            if not folder.is_relative_to(data) or folder==data:
                raise ValueError("Workspace must remain inside the data folder.")
            return folder

        def local_resource(self,folder,relative):
            target=(folder/relative).resolve()
            if not target.is_relative_to(folder):
                raise ValueError("File must remain inside the workspace.")
            return target

        def do_GET(self):
            if not self.trusted_host():
                return self.send(403,{"error":"Local host only"})
            origin=self.headers.get("Origin")
            allowed=(f"http://127.0.0.1:{self.server.server_port}",f"http://localhost:{self.server.server_port}")
            if (origin and origin not in allowed) or self.headers.get("Sec-Fetch-Site")=="cross-site":
                return self.send(403,{"error":"Local UI only"})
            path=unquote(urlparse(self.path).path)
            try:
                if path=="/api/state":
                    runs=[]
                    for folder in sorted(data.iterdir()):
                        if folder.is_dir() and (folder/"config.json").exists():
                            if folder.is_symlink() or not folder.resolve().is_relative_to(data):
                                continue
                            run=Run(folder)
                            runs.append({"name":folder.name,"model":run.config["model"],
                                "count":len(run.records()),"built":(folder/"reference.npz").exists()})
                    return self.send(200,{"runs":runs,"job":jobs.state,"token":token,'models_installed':models_installed})
                if path.startswith("/api/map/"):
                    run=self.run_path(path.split("/")[-1])
                    return self.send(200,read_json(self.local_resource(run,"map.json")))
                if path.startswith("/image/"):
                    _,_,name,filename=path.split("/")
                    slug(Path(filename).stem)
                    if not filename.endswith(".png"):
                        raise ValueError("PNG only")
                    folder=self.run_path(name)
                    return self.send(200,self.local_resource(folder,Path("images")/filename).read_bytes(),"image/png")
                if path=="/api/example":
                    example=Path(__file__).parent/"web"/"example.csv"
                    return self.send(200,example.read_bytes(),"text/csv; charset=utf-8")
                relative="index.html" if path=="/" else path.lstrip("/")
                file=(static/relative).resolve()
                if not file.is_relative_to(static.resolve()) or not file.is_file():
                    return self.send(404,{"error":"Not found"})
                return self.send(200,file.read_bytes(),mimetypes.guess_type(str(file))[0] or "application/octet-stream")
            except (ValueError,FileNotFoundError):
                self.send(404,{"error":"Not found"})

        def do_POST(self):
            origin=self.headers.get("Origin")
            allowed=(f"http://127.0.0.1:{self.server.server_port}",f"http://localhost:{self.server.server_port}")
            if not self.trusted_host() or (origin and origin not in allowed) or self.headers.get("X-LE-Token")!=token:
                return self.send(403,{"error":"Open the local UI and retry."})
            try:
                size=int(self.headers.get("Content-Length","0"))
                if self.headers.get_content_type()!="application/json":
                    raise ValueError("Use application/json.")
                if self.headers.get("Transfer-Encoding"):
                    raise ValueError("Chunked requests are not supported.")
                if not 0<size<=32_000_000:
                    raise ValueError("Request must be below 32 MB. Use the CLI for larger image batches.")
                body=json.loads(self.rfile.read(size))
                if not isinstance(body,dict):
                    raise ValueError("Expected a JSON object.")
                path=urlparse(self.path).path
                if path=="/api/stop":
                    jobs.stop.set(); return self.send(200,{"ok":True})
                if jobs.state["status"]=="running":
                    raise ValueError("A task is already running.")
                name=slug(body["name"])
                folder=self.run_path(name)
                if path=="/api/create":
                    Run.create(folder,new_config(body["model"],body.get("source") or None,body.get("device","auto"),memory_mode=body.get('memory_mode','standard')))
                elif path=="/api/generate":
                    from .models import generate
                    prompts=parse_prompts(body["text"],body.get("suffix",".csv"))
                    seeds=[int(s.strip()) for s in body.get("seeds","42").split(",")]
                    run=Run(folder)
                    query=bool(body.get("query"))
                    jobs.start("Preparing model",lambda p,c:generate(run,prompts,seeds,query,p,c))
                elif path=="/api/build":
                    jobs.start("Building reference and map",lambda p,c:Run(folder).freeze())
                elif path=="/api/import":
                    from .models import import_images
                    Run(folder)
                    if not (folder/"reference.npz").exists():
                        raise ValueError("Build the reference before importing test images.")
                    files=body["files"]
                    if not files or len(files)>100:
                        raise ValueError("Choose 1–100 images per upload.")
                    upload=self.local_resource(folder,"uploads"); upload.mkdir(exist_ok=True)
                    paths=[]
                    for index,file in enumerate(files):
                        suffix=Path(file["name"]).suffix.lower()
                        if suffix not in (".png",".jpg",".jpeg",".webp"):
                            raise ValueError("Choose PNG, JPEG or WebP images.")
                        content=base64.b64decode(file["data"],validate=True)
                        import hashlib
                        target=upload/(hashlib.sha256(content).hexdigest()[:20]+".png")
                        with Image.open(io.BytesIO(content)) as image:
                            clean_image(image).save(target,"PNG")
                        paths.append(target)
                    jobs.start("Importing images",lambda p,c:import_images(Run(folder),paths,p,c))
                else:
                    return self.send(404,{"error":"Unknown operation"})
                self.send(200,{"ok":True})
            except Exception as exc:
                self.send(400,{"error":str(exc)})
    return Handler

def serve(data=None,port=8877,open_browser=True):
    data=Path(data) if data is not None else default_data_dir(); data.mkdir(parents=True,exist_ok=True)
    class LocalServer(ThreadingHTTPServer):
        allow_reuse_address=False
    server=LocalServer(("127.0.0.1",port),handler_class(data,Jobs()))
    url=f"http://127.0.0.1:{server.server_port}"
    print(f"Language Edge: {url}\nData: {data.resolve()}\nCtrl+C to stop",flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
