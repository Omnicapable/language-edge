import argparse
import json
from pathlib import Path
from .core import Run, parse_prompts, slug, default_data_dir

def main():
    parser=argparse.ArgumentParser(description="Language Edge experimental VAE coverage explorer")
    sub=parser.add_subparsers(dest="command",required=True)
    init=sub.add_parser("create")
    init.add_argument("run"); init.add_argument("--model",choices=["sdxl-turbo","sd15"],required=True)
    init.add_argument("--source"); init.add_argument("--device",default="auto"); init.add_argument("--size",type=int,default=512)
    gen=sub.add_parser("generate")
    gen.add_argument("run"); gen.add_argument("prompts"); gen.add_argument("--seeds",default="42"); gen.add_argument("--query",action="store_true")
    for name in ("build","export"):
        sub.add_parser(name).add_argument("run")
    imp=sub.add_parser("import-images"); imp.add_argument("run"); imp.add_argument("images",nargs="+")
    serve=sub.add_parser("serve"); serve.add_argument("--data",default=str(default_data_dir())); serve.add_argument("--port",type=int,default=8877)
    serve.add_argument("--no-browser",action="store_true")
    args=parser.parse_args()
    try:
        if args.command=="serve":
            from .server import serve
            serve(args.data,args.port,not args.no_browser)
        elif args.command=="create":
            from .models import new_config
            Run.create(args.run,new_config(args.model,args.source,args.device,args.size))
            print("Created",args.run)
        elif args.command=="generate":
            from .models import generate
            source=Path(args.prompts)
            generate(Run(args.run),parse_prompts(source.read_text(encoding="utf-8-sig"),source.suffix),
                [int(s.strip()) for s in args.seeds.split(",")],args.query)
        elif args.command=="build":
            Run(args.run).freeze(); print("Reference built")
        elif args.command=="export":
            print(json.dumps(Run(args.run).export(),indent=2))
        elif args.command=="import-images":
            from .models import import_images
            import_images(Run(args.run),args.images)
    except (ValueError,OSError,ImportError) as exc:
        parser.exit(2,f"Error: {exc}\n")

if __name__=="__main__":
    main()
