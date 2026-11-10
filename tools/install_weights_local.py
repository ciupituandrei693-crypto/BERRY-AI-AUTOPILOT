"""Download only user-approved public model weights to a local folder.

Run by INSTALARE_COMPONENTE_LOCALE.ps1. This helper never performs inference,
launches servers, authenticates to a paid service, or executes downloaded code.
Upstream model cards and voice licenses must be reviewed before commercial use.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

MODELS = {
    "whisper_small": ("Systran/faster-whisper-small", None),
    "piper_ro": ("rhasspy/piper-voices", ["ro/ro_RO/**"]),
    "liveportrait": ("KlingTeam/LivePortrait", None),
    "musetalk": ("TMElyralab/MuseTalk", None),
    "latentsync_16": ("ByteDance/LatentSync-1.6", None),
    "hunyuan3d_mini": ("tencent/Hunyuan3D-2mini", ["hunyuan3d-dit-v2-mini/**"]),
    "ace_step": ("ACE-Step/ACE-Step-v1-3.5B", None),
}


def download_model(name: str, destination: Path) -> dict:
    if name not in MODELS:
        raise ValueError("Model necunoscut; numai modelele din lista fixa sunt permise")
    from huggingface_hub import snapshot_download
    repo, patterns = MODELS[name]
    destination = destination.expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "0"
    # Explicitly disable implicit token use; gated repositories require a
    # separate, user-managed approval and are not fetched here.
    path = snapshot_download(
        repo_id=repo, repo_type="model", local_dir=str(destination),
        allow_patterns=patterns, max_workers=2, token=False,
    )
    files = [p for p in Path(path).rglob("*")
             if p.is_file() and ".cache" not in p.parts]
    return {"engine": name, "repository": repo, "destination": str(destination),
            "files": len(files), "bytes": sum(p.stat().st_size for p in files),
            "downloaded_only": True, "inference_tested": False,
            "commercial_license_checked": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=sorted(MODELS))
    parser.add_argument("--dest", required=True)
    args = parser.parse_args()
    try:
        result = download_model(args.name, Path(args.dest))
    except Exception as exc:
        print(json.dumps({"engine": args.name, "status": "FAILED",
                          "error_type": type(exc).__name__,
                          "detail": str(exc)[:350]}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "DOWNLOADED", **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
