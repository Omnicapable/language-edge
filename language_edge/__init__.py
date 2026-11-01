"""Language Edge: experimental VAE prompt-coverage explorer."""
import os
# Set before optional Hugging Face libraries are imported. No app analytics are used.
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("DO_NOT_TRACK", "1")
__version__ = "0.1.3"
