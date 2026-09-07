"""Local inference using the original working Nepali VITS implementation."""
import json
import os
from pathlib import Path
import runpy
import sys
import types
import unicodedata
from urllib.request import urlretrieve

import numpy as np
import soundfile as sf
import torch
from huggingface_hub import hf_hub_download

def _load_vits(device, cache_root):
    repo = "Dragneel/nepali-vits-tts"
    cache = cache_root / "vits"
    cache.mkdir(parents=True, exist_ok=True)
    for name in ("models.py", "commons.py", "modules.py", "attentions.py", "transforms.py"):
        path = cache / name
        if not path.exists():
            urlretrieve("https://raw.githubusercontent.com/jaywalnut310/vits/main/" + name, path)
    # Upstream imports a compiled alignment extension used only during training.
    # Inference uses commons.generate_path and needs no compiler.
    alignment = types.ModuleType("monotonic_align")
    def training_only(*args, **kwargs):
        raise RuntimeError("Training alignment is unavailable in this inference-only runner")
    alignment.maximum_path = training_only
    sys.modules["monotonic_align"] = alignment
    sys.path.insert(0, str(cache))
    from models import SynthesizerTrn
    import commons
    config = json.loads(Path(hf_hub_download(repo, cache_dir=cache_root / "huggingface" / "hub", revision="2a25b14d913131f0673ef2bcab7b2fa4eade28d1", filename="nepali_base.json")).read_text())
    symbols = runpy.run_path(hf_hub_download(repo, cache_dir=cache_root / "huggingface" / "hub", revision="2a25b14d913131f0673ef2bcab7b2fa4eade28d1", filename="nepali_symbols.py"))["symbols"]
    clean = runpy.run_path(hf_hub_download(repo, cache_dir=cache_root / "huggingface" / "hub", revision="2a25b14d913131f0673ef2bcab7b2fa4eade28d1", filename="nepali_cleaners.py"))["nepali_cleaners"]
    vocab = {s: i for i, s in enumerate(symbols)}
    data = config["data"]
    model = SynthesizerTrn(len(symbols), data["filter_length"] // 2 + 1,
                           config["train"]["segment_size"] // data["hop_length"],
                           **config["model"])
    state = torch.load(hf_hub_download(repo, cache_dir=cache_root / "huggingface" / "hub", revision="2a25b14d913131f0673ef2bcab7b2fa4eade28d1", filename="G_100000.pth"), map_location="cpu", weights_only=True)
    model.load_state_dict(state["model"], strict=True)
    model.to(device).eval()
    def speak(text):
        text = clean(unicodedata.normalize("NFC", text))
        missing = sorted(set(text) - set(vocab))
        if missing:
            print("VITS unsupported characters omitted: " + repr("".join(missing)), flush=True)
        tokens = commons.intersperse([vocab[c] for c in text if c in vocab], 0)
        x = torch.tensor([tokens], dtype=torch.long, device=device)
        lengths = torch.tensor([len(tokens)], dtype=torch.long, device=device)
        return model.infer(x, lengths, noise_scale=0.667, noise_scale_w=0.8,
                           length_scale=1.0)[0][0, 0].cpu().numpy()
    return speak, data["sampling_rate"]



class VITS:
    """Load VITS on first synthesis; cache defaults to outputs/.cache in cwd."""

    def __init__(self, device="cpu", cache_dir=None):
        self.device = device
        self.cache_dir = Path(cache_dir or os.environ.get("NEPALI_SPEECH_CACHE", "outputs/.cache"))
        self._speak = None
        self.sample_rate = None

    def synthesize(self, text, output_path):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a nonempty string")
        if any(c.isascii() and c.isalpha() for c in text):
            raise ValueError("Latin text must be converted with prepare_text first")
        torch.set_num_threads(min(4, os.cpu_count() or 1))
        if self._speak is None:
            self._speak, self.sample_rate = _load_vits(self.device, self.cache_dir)
        with torch.inference_mode():
            audio = np.asarray(self._speak(text), dtype=np.float32).reshape(-1)
        if not audio.size or not np.isfinite(audio).all() or not np.any(audio):
            raise RuntimeError("VITS produced empty, nonfinite, or silent audio")
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(path, audio, self.sample_rate, subtype="PCM_16")
        return path
