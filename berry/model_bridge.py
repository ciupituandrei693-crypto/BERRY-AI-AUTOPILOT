"""Opt-in LOCAL model bridge for LivePortrait, MuseTalk, LatentSync, Hunyuan3D.

Uses user-configured Python environments and argv arrays; NEVER a shell, auto
installer, remote service, or download. Configuration is intentionally explicit
because upstream model CLIs and checkpoints change between versions.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

KINDS = {
    "liveportrait": ("video", ("image", "video")),
    "musetalk": ("video", ("video", "voice")),
    "latentsync": ("video", ("video", "voice")),
    "hunyuan3d": ("mesh", ("image",)),
}
TOKENS = ("{image}", "{video}", "{voice}", "{output}", "{outdir}", "{yaml}")
MAX_CONFIG_BYTES = 100_000
MAX_MEDIA_BYTES = 500_000_000


class BridgeError(ValueError):
    pass


def _configuration() -> dict:
    path = os.getenv("BERRY_MODEL_BRIDGE_CONFIG", "").strip()
    if not path:
        return {}
    p = Path(path).expanduser()
    if not p.is_file() or p.stat().st_size > MAX_CONFIG_BYTES:
        raise BridgeError("Configurația bridge lipsește sau este prea mare")
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BridgeError("Configurație JSON invalidă") from exc
    if not isinstance(obj, dict) or not isinstance(obj.get("engines"), dict):
        raise BridgeError("Configurația trebuie să conțină obiectul engines")
    return obj["engines"]


def _within(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _validate(name: str) -> dict:
    if name not in KINDS:
        raise BridgeError("Motor necunoscut")
    spec = _configuration().get(name)
    if not isinstance(spec, dict):
        raise BridgeError("Lipsește configurarea acestui motor")
    root_raw, python_raw = spec.get("root"), spec.get("python")
    if not isinstance(root_raw, str) or not isinstance(python_raw, str):
        raise BridgeError("Sunt necesare root și python")
    if any(v.startswith(("\\\\", "//")) or "://" in v for v in (root_raw, python_raw)):
        raise BridgeError("Căile de rețea sau URL sunt interzise")
    root, python = Path(root_raw).expanduser().resolve(), Path(python_raw).expanduser().resolve()
    if not root.is_dir() or not python.is_file() or python.suffix.lower() not in (".exe", ""):
        raise BridgeError("Folderul motorului sau interpretorul Python nu există")
    argv = spec.get("argv")
    if not isinstance(argv, list) or not 2 <= len(argv) <= 70:
        raise BridgeError("argv trebuie să fie o listă de argumente")
    if any(not isinstance(x, str) or not x or len(x) > 1000
           or any(c in x for c in ("\x00", "\r", "\n"))
           or "://" in x for x in argv):
        raise BridgeError("Argument invalid sau adresă externă interzisă")
    if argv[0] == "-m":
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", argv[1]):
            raise BridgeError("Modul Python invalid")
    else:
        entry = (root / argv[0]).resolve()
        if not argv[0].endswith(".py") or not _within(root, entry) or not entry.is_file():
            raise BridgeError("Primul argument trebuie să fie un script .py din root sau -m")
    if not any("{output}" in x or "{outdir}" in x for x in argv):
        raise BridgeError("argv trebuie să conțină {output} sau {outdir}")
    weights = spec.get("weights", [])
    if not isinstance(weights, list) or not 1 <= len(weights) <= 30:
        raise BridgeError("Declară cel puțin un checkpoint local în weights")
    for rel in weights:
        if not isinstance(rel, str) or not rel or len(rel) > 300:
            raise BridgeError("Cale weights invalidă")
        f = (root / rel).resolve()
        if not _within(root, f) or not f.is_file():
            raise BridgeError("Lipsește cel puțin un checkpoint local")
    return {"root": root, "python": python, "argv": argv, "weights": weights}


def status(name: str) -> dict:
    try:
        spec = _validate(name)
        return {"configured": True, "online": False, "ready": True,
                "detail": "Config local validat; inferența pe GPU NU este încă verificată",
                "requires_local_models": True, "weights_declared": len(spec["weights"])}
    except (BridgeError, OSError) as exc:
        return {"configured": name in _configuration_safe(), "online": False,
                "ready": False, "detail": str(exc)[:180], "requires_local_models": True}


def _configuration_safe() -> dict:
    try:
        return _configuration()
    except (BridgeError, OSError):
        return {}


def _asset(item_id: int, kind: str, root: Path) -> Path:
    candidates = {
        "image": [root / ("item_%s.webp" % item_id), root / ("item_%s.png" % item_id)],
        "voice": [root / ("item_%s_voice.wav" % item_id), root / ("item_%s_voice.mp3" % item_id)],
        "video": [root / ("item_%s_video.mp4" % item_id)],
    }[kind]
    for p in candidates:
        if p.is_file() and 100 <= p.stat().st_size <= MAX_MEDIA_BYTES:
            return p.resolve()
    raise BridgeError("Lipsește fișierul local necesar: " + kind)


def run(name: str, item: dict, job_id: int) -> dict:
    """Execute only on explicit creative job request. No background auto-trigger."""
    spec = _validate(name)
    from .creative import assets_dir
    from . import studio
    assets = assets_dir().resolve()
    output_root = Path(os.getenv("BERRY_OUTPUT_DIR", str(studio.OUTPUT_ROOT))).expanduser().resolve()
    work = output_root / ("bridge_%s_%06d" % (name, job_id))
    work.mkdir(parents=True, exist_ok=True)
    kind, needed = KINDS[name]
    values = {"{outdir}": str(work), "{output}": str(work / ("output.mp4" if kind == "video" else "output.glb"))}
    for key in needed:
        values["{" + key + "}"] = str(_asset(int(item["id"]), key, assets))
    if "{yaml}" in " ".join(spec["argv"]):
        if "video" not in needed or "voice" not in needed:
            raise BridgeError("Șablonul YAML necesită video și voice")
        yaml_path = work / "inference.yaml"
        yaml_path.write_text("task_0:\n video_path: " + json.dumps(values["{video}"]) +
                             "\n audio_path: " + json.dumps(values["{voice}"]) + "\n", encoding="utf-8")
        values["{yaml}"] = str(yaml_path)
    argv = []
    for token in spec["argv"]:
        for key, value in values.items():
            token = token.replace(key, value)
        if any(x in token for x in TOKENS):
            raise BridgeError("Placeholder necunoscut sau intrare lipsă")
        argv.append(token)
    environment = os.environ.copy()
    environment.update({
        "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
        "HF_DATASETS_OFFLINE": "1", "WANDB_MODE": "offline",
        "PIP_NO_INDEX": "1", "DO_NOT_TRACK": "1",
    })
    timeout = min(7200, max(60, int(os.getenv("BERRY_BRIDGE_TIMEOUT", "1800"))))
    started = time.monotonic()
    try:
        result = subprocess.run([str(spec["python"]), *argv], cwd=str(spec["root"]),
                                env=environment, capture_output=True, text=True,
                                errors="replace", timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise BridgeError("Motorul a depășit timpul maxim local") from exc
    except OSError as exc:
        raise BridgeError("Motorul local nu a putut fi pornit") from exc
    # Logs stay on the user's PC; do not return private paths or model prompts in HTTP.
    (work / "model_log.txt").write_text(((result.stdout or "") + "\n" +
                                          (result.stderr or ""))[-16000:], encoding="utf-8")
    if result.returncode:
        raise BridgeError("Inferența locală a eșuat; consultă model_log.txt")
    extension = ".mp4" if kind == "video" else ".glb"
    target = Path(values["{output}"])
    candidates = [target] if target.is_file() else list(work.rglob("*" + extension))
    candidates = [p for p in candidates if p.is_file() and _within(work, p) and
                  1000 <= p.stat().st_size <= MAX_MEDIA_BYTES]
    if not candidates:
        raise BridgeError("Motorul nu a creat un fișier de ieșire valid în folderul local")
    source = max(candidates, key=lambda p: p.stat().st_size)
    with source.open("rb") as handle:
        header = handle.read(32)
    if kind == "video" and b"ftyp" not in header[:20]:
        raise BridgeError("Ieșirea nu are antet MP4 valid")
    if kind == "mesh" and not header.startswith(b"glTF"):
        raise BridgeError("Ieșirea nu are antet GLB valid")
    dest = assets / ("item_%s_%s.%s" % (item["id"], "video" if kind == "video" else "mesh",
                                       "mp4" if kind == "video" else "glb"))
    temp = assets / (dest.name + ".partial")
    shutil.copyfile(source, temp)
    temp.replace(dest)
    provenance = {"engine": name, "kind": kind, "filename": dest.name,
                  "local_only": True, "published": False, "review_required": True,
                  "model_inference_completed": True, "hardware_verified": True,
                  "elapsed_seconds": round(time.monotonic() - started, 2)}
    (assets / ("item_%s_%s_source.json" % (item["id"], kind))).write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    return provenance
