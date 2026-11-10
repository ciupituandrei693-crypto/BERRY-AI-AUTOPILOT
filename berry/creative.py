"""Opt-in local AI media adapters. Each job is explicit; no cloud or auto-posting.

ComfyUI API image workflow, ACE-Step 1.5 REST music, WanGP in-process API,
and faster-whisper CPU transcription. Engines and weights are NOT bundled.
"""
from __future__ import annotations

import io
import json
import os
import random
import shutil
import subprocess
import threading
import time
from pathlib import Path
from urllib.parse import urlencode

from PIL import Image, ImageOps, UnidentifiedImageError

from . import db, engines, studio

ROOT = Path(__file__).resolve().parents[1]
LOCK = threading.Lock()
ENGINES = ("comfyui", "ace_step", "wangp", "faster_whisper", "voice_studio", "blender_3d")


def assets_dir() -> Path:
    root = Path(os.getenv("BERRY_ASSET_DIR", str(ROOT / "data" / "assets")))
    root.mkdir(parents=True, exist_ok=True)
    return root


def init() -> None:
    with db.connection() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS creative_jobs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL REFERENCES items(id),
            engine TEXT NOT NULL, status TEXT NOT NULL, result_json TEXT, error TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        con.execute("UPDATE creative_jobs SET status='INTERRUPTED',updated_at=? WHERE status IN ('RUNNING','QUEUED')",
                    (db.utcnow(),))


def jobs() -> list[dict]:
    rows = db.all_rows("SELECT j.*,i.title FROM creative_jobs j JOIN items i ON i.id=j.item_id ORDER BY j.id DESC LIMIT 60")
    for row in rows:
        row["result"] = json.loads(row.pop("result_json") or "null")
    return rows


def _mark(job_id: int, status: str, result: dict | None = None, error: str = "") -> None:
    with db.connection() as con:
        con.execute("UPDATE creative_jobs SET status=?,result_json=?,error=?,updated_at=? WHERE id=?",
                    (status, json.dumps(result, ensure_ascii=False) if result else None, error[:400], db.utcnow(), job_id))
        db.audit(con, "local_ai_job_status", {"id": job_id, "status": status})


def _invalidate(item_id: int, source: str) -> None:
    with db.connection() as con:
        con.execute("UPDATE render_jobs SET status='STALE',updated_at=? WHERE item_id=? AND status IN ('DONE','PACKAGE_ONLY')",
                    (db.utcnow(), item_id))
        db.audit(con, "local_ai_asset_created", {"item_id": item_id, "source": source})


def start(item_id: int, engine: str) -> dict:
    if engine not in ENGINES:
        raise ValueError("Motor AI necunoscut")
    item = db.one_row("SELECT * FROM items WHERE id=?", (item_id,))
    if not item:
        raise LookupError("Materialul nu există")
    if item["status"] != "DRAFT":
        raise ValueError("AI local poate modifica numai materiale DRAFT")
    if engine == "ace_step" and item["channel_id"] != "beats":
        raise ValueError("ACE-Step este destinat canalului FRUIT BEATS")
    ready = engines.statuses()[engine]["ready"]
    if not ready:
        raise ValueError("Motorul nu este pregătit; verifică Local AI Engines și modelele instalate")
    with LOCK:
        if db.one_row("SELECT id FROM creative_jobs WHERE status IN ('QUEUED','RUNNING')"):
            raise ValueError("Există deja o generare AI locală în curs")
        with db.connection() as con:
            now = db.utcnow()
            cur = con.execute("INSERT INTO creative_jobs(item_id,engine,status,created_at,updated_at) VALUES(?,?,?,?,?)",
                              (item_id, engine, "QUEUED", now, now))
            job_id = cur.lastrowid
            db.audit(con, "local_ai_job_queued", {"id": job_id, "engine": engine, "item_id": item_id})
    threading.Thread(target=_worker, args=(job_id, item), daemon=True, name=f"berry-ai-{job_id}").start()
    return {"job_id": job_id, "engine": engine, "status": "QUEUED", "local_only": True}


def _worker(job_id: int, item: dict) -> None:
    with LOCK:
        row = db.one_row("SELECT engine FROM creative_jobs WHERE id=?", (job_id,))
        if not row:
            return
        engine = row["engine"]
        _mark(job_id, "RUNNING")
        started = time.monotonic()
        try:
            if engine == "comfyui":
                result = comfyui_image(item)
            elif engine == "ace_step":
                result = ace_step_music(item)
            elif engine == "wangp":
                result = wangp_video(item, job_id)
            elif engine == "voice_studio":
                result = voicestudio_tts(item)
            elif engine == "blender_3d":
                from . import three_d
                result = three_d.render_item(item, job_id)
            else:
                result = whisper_subtitles(item, job_id)
            result["elapsed_seconds"] = round(time.monotonic() - started, 2)
            if engine == "blender_3d" and result["elapsed_seconds"] > 0:
                result["measured_render_fps"] = round(result["rendered_frames"] / result["elapsed_seconds"], 2)
            result["model_benchmark_on_this_pc"] = engine != "blender_3d"
            _invalidate(item["id"], engine)
            _mark(job_id, "DONE", result)
        except Exception as exc:
            # No environment secrets, command lines or private absolute paths in the API.
            msg = str(exc)
            if isinstance(exc, (engines.EngineError, ValueError, TimeoutError)):
                _mark(job_id, "FAILED", error=msg)
            else:
                _mark(job_id, "FAILED", error=f"Motorul {engine} a eșuat ({type(exc).__name__}); verifică logurile locale")


def _prompt(item: dict) -> str:
    from .db import CHANNELS, CHARACTERS
    lead = next(c[3] for c in CHANNELS if c[0] == item["channel_id"])
    look = next((c[2] for c in CHARACTERS if c[0] == lead), "personaj-fruct original")
    return (f"Cinematic 3D anthropomorphic fruit character {lead}; {look}. "
            f"Consistent original character design, vertical 9:16, expressive face, realistic studio lighting, "
            f"detailed scene about {item['topic'][:220]}. No logos, no watermarks, no real people.")


def _workflow(item: dict) -> dict:
    path = Path(os.environ.get("BERRY_COMFYUI_WORKFLOW", "")).expanduser()
    if not path.is_file() or path.stat().st_size > 1_000_000:
        raise ValueError("Workflow ComfyUI API JSON lipsă sau prea mare")
    try:
        workflow = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Workflow ComfyUI invalid") from exc
    if not isinstance(workflow, dict) or not workflow or len(workflow) > 250:
        raise ValueError("Workflow API ComfyUI trebuie să fie un obiect cu noduri")
    prompt = _prompt(item)
    values = {"{{PROMPT}}": prompt, "{{NEGATIVE_PROMPT}}": "blurry, low quality, extra limbs, text, watermark",
              "{{SEED}}": random.SystemRandom().randint(1, 2**31-1), "{{WIDTH}}": 576, "{{HEIGHT}}": 1024,
              "{{PREFIX}}": f"berry_{item['id']}"}
    def replace(value):
        if isinstance(value, dict):
            return {k: replace(v) for k, v in value.items()}
        if isinstance(value, list):
            return [replace(v) for v in value]
        if isinstance(value, str):
            if value in values:
                return values[value]
            for key, replacement in values.items():
                value = value.replace(key, str(replacement))
        return value
    workflow = replace(workflow)
    if not all(isinstance(v, dict) and "class_type" in v for v in workflow.values()):
        raise ValueError("Folosește Export API din ComfyUI, nu workflow-ul UI")
    return workflow


def comfyui_image(item: dict) -> dict:
    workflow = _workflow(item)
    response = engines.json_request("comfyui", "/prompt", payload={"prompt": workflow, "client_id": "berry-local"}, timeout=25)
    pid = response.get("prompt_id")
    if not isinstance(pid, str) or not pid or len(pid) > 128 or not all(c.isalnum() or c in "-_" for c in pid):
        raise engines.EngineError("ComfyUI nu a acceptat workflow-ul (prompt_id invalid)")
    history = None
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        data = engines.json_request("comfyui", f"/history/{pid}", timeout=10)
        history = data.get(pid)
        if isinstance(history, dict):
            break
        time.sleep(2)
    if not isinstance(history, dict):
        raise TimeoutError("ComfyUI nu a terminat în 10 minute")
    if history.get("status", {}).get("status_str") == "error":
        raise engines.EngineError("ComfyUI a raportat eroare de execuție")
    images = [img for output in history.get("outputs", {}).values() if isinstance(output, dict)
              for img in output.get("images", []) if isinstance(img, dict)]
    if not images:
        raise engines.EngineError("Workflow-ul nu a generat o imagine SaveImage")
    img = images[0]
    if img.get("type", "output") != "output":
        raise engines.EngineError("ComfyUI trebuie să salveze în output")
    filename, subfolder = str(img.get("filename", "")), str(img.get("subfolder", ""))
    if (not filename or len(filename) > 180 or any(c in filename for c in ("/", "\\", "\x00"))
            or ".." in filename or ".." in subfolder or subfolder.startswith(("/", "\\"))
            or "\\" in subfolder or len(subfolder) > 160):
        raise engines.EngineError("Nume fișier ComfyUI invalid")
    path = "/view?" + urlencode({"filename": filename, "subfolder": subfolder, "type": "output"})
    raw = engines.request("comfyui", path, timeout=35, max_bytes=16_000_000)
    try:
        with Image.open(io.BytesIO(raw)) as source:
            if source.width * source.height > 25_000_000:
                raise ValueError("Imagine prea mare")
            picture = ImageOps.exif_transpose(source).convert("RGB")
            picture.thumbnail((2048, 2048))
    except (UnidentifiedImageError, OSError) as exc:
        raise engines.EngineError("ComfyUI a returnat imagine invalidă") from exc
    dest = assets_dir() / f"item_{item['id']}.webp"
    picture.save(dest, format="WEBP", quality=91)
    (assets_dir() / f"item_{item['id']}_art_source.json").write_text(json.dumps({"engine":"ComfyUI"}), encoding="utf-8")
    return {"kind": "AI_IMAGE_LOCAL", "filename": dest.name, "engine": "ComfyUI", "published": False,
            "license_check_required": True, "prompt_id": pid}


def _unwrap(obj: dict):
    if "data" in obj:
        return obj["data"]
    return obj


def ace_step_music(item: dict) -> dict:
    from .studio import _script_lines
    lyrics = "\n".join(_script_lines(item))[:2500]
    body = {"prompt": f"Original royalty-cleared composition concept about {item['topic'][:200]}, upbeat fruit character solo, polished pop production",
            "lyrics": lyrics, "vocal_language": "ro", "audio_duration": 30, "inference_steps": 8,
            "task_type": "text2music", "use_random_seed": True}
    answer = _unwrap(engines.json_request("ace_step", "/release_task", payload=body, timeout=35))
    if not isinstance(answer, dict) or not isinstance(answer.get("task_id"), str):
        raise engines.EngineError("ACE-Step nu a returnat task_id")
    task_id = answer["task_id"]
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        response = _unwrap(engines.json_request("ace_step", "/query_result", payload={"task_id_list": [task_id]}, timeout=15))
        if not isinstance(response, list) or not response:
            raise engines.EngineError("ACE-Step a returnat rezultat invalid")
        task = response[0]
        status = int(task.get("status", 0))
        if status == 2:
            raise engines.EngineError("ACE-Step a eșuat")
        if status == 1:
            result = task.get("result", "[]")
            files = json.loads(result) if isinstance(result, str) else result
            if not isinstance(files, list) or not files or not files[0].get("file"):
                raise engines.EngineError("ACE-Step nu a produs audio")
            # ACE-Step serves the file from its own allowed temporary audio directory.
            audio_path = str(files[0]["file"])
            if len(audio_path) > 500:
                raise engines.EngineError("Cale audio invalidă")
            raw = engines.request("ace_step", "/v1/audio?" + urlencode({"path": audio_path}),
                                  timeout=60, max_bytes=60_000_000)
            ext = "wav" if raw.startswith(b"RIFF") and raw[8:12] == b"WAVE" else "mp3" if (
                raw.startswith(b"ID3") or (len(raw)>2 and raw[0] == 255 and (raw[1]&224) == 224)) else None
            if not ext:
                raise engines.EngineError("Audio generat trebuie să fie WAV sau MP3")
            for old in assets_dir().glob(f"item_{item['id']}_soundtrack.*"):
                old.unlink(missing_ok=True)
            dest = assets_dir() / f"item_{item['id']}_soundtrack.{ext}"
            dest.write_bytes(raw)
            (assets_dir() / f"item_{item['id']}_music_source.json").write_text(json.dumps({"engine":"ACE-Step 1.5"}), encoding="utf-8")
            return {"kind": "AI_MUSIC_LOCAL", "filename": dest.name, "engine": "ACE-Step 1.5",
                    "published": False, "license_check_required": True, "task_id": task_id}
        time.sleep(4)
    raise TimeoutError("ACE-Step nu a terminat în 15 minute")


def voicestudio_tts(item: dict) -> dict:
    """Use VoiceStudio's documented OpenAI-compatible LOCAL endpoint, never a cloud API."""
    text = " ".join(studio._script_lines(item))[:3900]
    if not text:
        raise ValueError("Scenariul este gol")
    voice = os.environ.get("BERRY_VOICESTUDIO_VOICE", "default").strip()[:100]
    model = os.environ.get("BERRY_VOICESTUDIO_MODEL", "tts-1").strip()[:100]
    audio = engines.request("voice_studio", "/v1/audio/speech", payload={
        "model": model, "input": text, "voice": voice, "response_format": "wav", "language": "ro"
    }, timeout=600, max_bytes=25_000_000)
    if not (audio.startswith(b"RIFF") and audio[8:12] == b"WAVE"):
        raise engines.EngineError("VoiceStudio nu a returnat un WAV valid")
    dest = assets_dir() / f"item_{item['id']}_voice.wav"
    dest.write_bytes(audio)
    return {"kind": "LOCAL_TTS", "filename": dest.name, "engine": "VoiceStudio",
            "published": False, "voice_rights_review_required": True, "text_truncated": len(text) == 3900}


def _run_external_python(env: str, script: Path, args: list[str], timeout: int) -> dict:
    python = Path(os.environ.get(env, "")).expanduser()
    if not python.is_file():
        raise ValueError(f"Configurează {env} cu calea către python.exe din mediul motorului")
    try:
        process = subprocess.run([str(python), str(script), *args], capture_output=True, text=True,
                                 timeout=timeout, check=False, cwd=str(ROOT))
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError("Motorul local a depășit limita de execuție") from exc
    if process.returncode:
        raise ValueError("Motorul local a eșuat; consultă jurnalul motorului instalat")
    # Workers print a single JSON object on the last line, no absolute paths in HTTP errors.
    try:
        return json.loads(process.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError) as exc:
        raise ValueError("Motorul local nu a returnat manifest JSON") from exc


def wangp_video(item: dict, job_id: int) -> dict:
    root = Path(os.environ.get("BERRY_WANGP_ROOT", "")).expanduser().resolve()
    settings = Path(os.environ.get("BERRY_WANGP_SETTINGS", "")).expanduser().resolve()
    if not (root.is_dir() and settings.is_file() and settings.suffix.lower() == ".json"):
        raise ValueError("Configurează folderul WanGP și Export Settings JSON")
    output = (assets_dir().parent / "ai_temp" / f"wangp_{job_id}").resolve()
    output.mkdir(parents=True, exist_ok=True)
    answer = _run_external_python("BERRY_WANGP_PYTHON", ROOT / "tools" / "wangp_worker.py",
                                  [str(root), str(settings), str(output), _prompt(item)], 3600)
    if not answer.get("success"):
        raise ValueError("WanGP nu a generat video")
    candidates = list(output.rglob("*.mp4"))
    if not candidates:
        raise ValueError("WanGP nu a salvat MP4 în directorul de ieșire")
    source = max(candidates, key=lambda p: p.stat().st_size)
    if source.stat().st_size > 500_000_000:
        raise ValueError("Video WanGP depășește limita locală de 500 MB")
    dest = assets_dir() / f"item_{item['id']}_video.mp4"
    shutil.copyfile(source, dest)
    (assets_dir() / f"item_{item['id']}_video_source.json").write_text(json.dumps({"engine":"WanGP"}), encoding="utf-8")
    return {"kind": "AI_VIDEO_LOCAL", "filename": dest.name, "engine": "WanGP", "published": False,
            "license_check_required": True, "duration_unverified": True}


def whisper_subtitles(item: dict, job_id: int) -> dict:
    voice = next((p for ext in ("wav", "mp3") if (p := assets_dir() / f"item_{item['id']}_voice.{ext}").is_file()), None)
    if voice is None:
        raise ValueError("Încarcă întâi o voce WAV/MP3 pentru transcriere")
    model = Path(os.environ.get("BERRY_WHISPER_MODEL", "")).expanduser().resolve()
    if not model.is_dir():
        raise ValueError("Configurează modelul faster-whisper local")
    dest = assets_dir() / f"item_{item['id']}_captions.srt"
    answer = _run_external_python("BERRY_WHISPER_PYTHON", ROOT / "tools" / "whisper_worker.py",
                                  [str(model), str(voice), str(dest)], 900)
    if not answer.get("success") or not dest.is_file():
        raise ValueError("Transcrierea nu a produs subtitrări")
    return {"kind": "TRANSCRIPTION_LOCAL", "filename": dest.name, "engine": "faster-whisper",
            "published": False, "review_required": True}
