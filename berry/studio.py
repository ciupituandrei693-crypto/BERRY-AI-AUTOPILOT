"""BERRY local-first media assembly v0.2.

Generates reviewable storyboard assets and, if FFmpeg is installed, a *static
concept preview* (NOT AI video). Does not download, post, spend, or use cloud.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from . import db

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static" / "img"
OUTPUT_ROOT = ROOT / "data" / "outputs"
ENGINE_LOCK = threading.Semaphore(1)

CHARACTER_ART = {
    "mind": "mind.webp", "wealth": "wealth.webp", "beats": "beats.webp",
    "lab": "lab.webp", "heart": "heart.webp",
}
LEADS = {
    "mind": "MUREX", "wealth": "BANAN", "beats": "AFINA STAR",
    "lab": "AFINA", "heart": "EMERA și CHERO",
}


def binary_path(name: str, env_name: str) -> str | None:
    configured = os.getenv(env_name, "").strip()
    if configured:
        # Explicit local executable paths only; no network or shell invocation.
        p = Path(configured).expanduser()
        return str(p) if p.is_file() else None
    return shutil.which(name)


def capabilities() -> dict:
    ffmpeg = binary_path("ffmpeg", "BERRY_FFMPEG_PATH")
    piper = binary_path("piper", "BERRY_PIPER_PATH")
    model = Path(os.getenv("BERRY_PIPER_MODEL", "")).expanduser() if os.getenv("BERRY_PIPER_MODEL") else None
    return {
        "ffmpeg": {"ready": bool(ffmpeg), "detail": "Randare locală MP4" if ffmpeg else "Instalează FFmpeg sau configurează BERRY_FFMPEG_PATH"},
        "piper": {"ready": bool(piper and model and model.is_file()), "detail": "TTS local, dacă vocea .onnx este configurată"},
        "koboldcpp": {"ready": False, "detail": "Adaptor disponibil; modelul local trebuie pornit separat"},
        "blender": {"ready": bool(binary_path("blender", "BERRY_BLENDER_PATH")), "detail": "Detectare instalare; rigging 3D nu este integrat"},
        "voice_studio": {"ready": False, "detail": "Sursă disponibilă, adaptor încă neintegrat"},
        "chatterbox": {"ready": False, "detail": "Sursă disponibilă, modele/integrare lipsă"},
        "faster_whisper": {"ready": False, "detail": "Sursă disponibilă; transcriere audio neintegrată"},
        "ace_step": {"ready": False, "detail": "Sursă disponibilă; generare muzică neintegrată"},
        "comfyui": {"ready": False, "detail": "Sursă disponibilă; modele și workflow neintegrate"},
        "wan_gp": {"ready": False, "detail": "Sursă disponibilă; modele și GPU neconfigurate"},
        "external_social": {"ready": False, "detail": "Dezactivat intenționat"},
        "cloud_gpu": {"ready": False, "detail": "Dezactivat intenționat"},
    }


def init_jobs() -> None:
    with db.connection() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS render_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL REFERENCES items(id),
            mode TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'QUEUED',
            output_relpath TEXT,
            result_json TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        # An interrupted render is never silently marked complete.
        con.execute("UPDATE render_jobs SET status='INTERRUPTED', updated_at=? WHERE status IN ('QUEUED','RUNNING')", (db.utcnow(),))


def get_jobs() -> list[dict]:
    rows = db.all_rows("""SELECT j.*,i.title,i.channel_id,i.content_type
                          FROM render_jobs j JOIN items i ON i.id=j.item_id
                          ORDER BY j.id DESC LIMIT 100""")
    for row in rows:
        row["result"] = json.loads(row.pop("result_json")) if row["result_json"] else None
    return rows


def get_job(job_id: int) -> dict | None:
    row = db.one_row("""SELECT j.*,i.title,i.channel_id,i.content_type
                         FROM render_jobs j JOIN items i ON i.id=j.item_id
                         WHERE j.id=?""", (job_id,))
    if row:
        row["result"] = json.loads(row.pop("result_json")) if row["result_json"] else None
    return row


def submit(item_id: int, mode: Literal["preview", "full"] = "preview") -> int:
    if mode not in ("preview", "full"):
        raise ValueError("Mod de randare invalid")
    item = db.one_row("SELECT * FROM items WHERE id=?", (item_id,))
    if not item:
        raise LookupError("Materialul nu există")
    if item["status"] != "DRAFT":
        raise ValueError("Randarea este permisă doar pentru materiale DRAFT; revizuiește separat loturile aprobate")
    with db.connection() as con:
        pending = con.execute("SELECT COUNT(*) FROM render_jobs WHERE status IN ('QUEUED','RUNNING')").fetchone()[0]
        if pending >= 3:
            raise ValueError("Există deja 3 randări în așteptare; încearcă mai târziu")
        now = db.utcnow()
        cursor = con.execute("INSERT INTO render_jobs(item_id,mode,created_at,updated_at) VALUES(?,?,?,?)", (item_id, mode, now, now))
        job_id = cursor.lastrowid
        db.audit(con, "local_render_queued", {"job_id": job_id, "item_id": item_id, "mode": mode})
    threading.Thread(target=_worker, args=(job_id,), name=f"berry-render-{job_id}", daemon=True).start()
    return job_id


def _set_status(job_id: int, status: str, *, result: dict | None = None, error: str | None = None, output: str | None = None) -> None:
    with db.connection() as con:
        con.execute("""UPDATE render_jobs SET status=?,result_json=?,error=?,output_relpath=?,updated_at=? WHERE id=?""",
                    (status, json.dumps(result, ensure_ascii=False) if result else None, error, output, db.utcnow(), job_id))
        db.audit(con, "local_render_status", {"job_id": job_id, "status": status})


def _script_lines(item: dict) -> list[str]:
    topic = " ".join(item["topic"].split())
    lead = LEADS[item["channel_id"]]
    return [
        f"{lead} prezintă: {topic}.",
        "Ce merită să știm înainte să tragem o concluzie?",
        f"Explorăm subiectul {topic} cu exemple ușor de urmărit.",
        "Separăm observațiile de presupuneri și verificăm informațiile importante.",
        "Tu ce întrebare ai despre acest subiect? Scrie-ne în comentarii.",
    ]


def _srt(lines: list[str], duration: int) -> str:
    def stamp(t: int) -> str:
        ms = t * 1000
        return f"{ms // 3600000:02}:{(ms // 60000) % 60:02}:{(ms // 1000) % 60:02},{ms % 1000:03}"
    chunks = []
    for idx, line in enumerate(lines):
        start = round(idx * duration / len(lines))
        end = round((idx + 1) * duration / len(lines))
        if end <= start:
            end = start + 1
        chunks.append(f"{idx + 1}\n{stamp(start)} --> {stamp(end)}\n{line}\n")
    return "\n".join(chunks) + "\n"


def _piper_audio(outdir: Path, text: str) -> Path | None:
    piper = binary_path("piper", "BERRY_PIPER_PATH")
    model_value = os.getenv("BERRY_PIPER_MODEL", "")
    if not (piper and model_value):
        return None
    model = Path(model_value).expanduser()
    if not model.is_file():
        return None
    dest = outdir / "voice.wav"
    proc = subprocess.run([piper, "--model", str(model), "--output_file", str(dest)],
                          input=text, text=True, capture_output=True, timeout=120, check=False)
    if proc.returncode or not dest.is_file() or dest.stat().st_size == 0:
        raise RuntimeError("Piper a eșuat. Verifică vocea locală și configurația.")
    return dest


def _ffmpeg_render(outdir: Path, art: Path, duration: int, voice: Path | None) -> Path:
    ffmpeg = binary_path("ffmpeg", "BERRY_FFMPEG_PATH")
    if not ffmpeg:
        raise FileNotFoundError("FFmpeg indisponibil")
    output = outdir / "concept-preview.mp4"
    # Fixed local input/output paths and arguments: never run user-provided commands.
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-loop", "1", "-framerate", "12", "-i", str(art)]
    if voice:
        cmd += ["-i", str(voice), "-filter_complex", "[1:a]apad[a]", "-map", "0:v:0", "-map", "[a]"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
    cmd += ["-t", str(duration), "-vf", "scale=360:640:force_original_aspect_ratio=increase,crop=360:640,setsar=1",
            "-r", "12", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "27", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(output)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=max(60, duration * 4), check=False)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("FFmpeg a depășit timpul maxim de randare") from exc
    if proc.returncode or not output.is_file() or output.stat().st_size < 1000:
        raise RuntimeError("FFmpeg: " + (proc.stderr or "randare eșuată")[-700:])
    return output


def _worker(job_id: int) -> None:
    with ENGINE_LOCK:
        try:
            _set_status(job_id, "RUNNING")
            job = get_job(job_id)
            if not job:
                return
            item = db.one_row("SELECT * FROM items WHERE id=?", (job["item_id"],))
            if not item:
                raise LookupError("Materialul a fost șters")
            output_root = Path(os.getenv("BERRY_OUTPUT_DIR", str(OUTPUT_ROOT))).resolve()
            outdir = output_root / f"job_{job_id:06d}"
            outdir.mkdir(parents=True, exist_ok=True)
            art = STATIC / CHARACTER_ART[item["channel_id"]]
            if not art.is_file():
                raise FileNotFoundError("Imaginea concept a personajului lipsește")
            lines = _script_lines(item)
            target = {"main90": 90, "short15": 15, "image": 0, "longform": 300}[item["content_type"]]
            duration = min(target, max(2, min(15, int(os.getenv("BERRY_PREVIEW_MAX_SECONDS", "8"))))) if job["mode"] == "preview" else target
            (outdir / "script.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
            shutil.copyfile(art, outdir / "character-concept.webp")
            if duration:
                (outdir / "captions.srt").write_text(_srt(lines, duration), encoding="utf-8")
            voice = None
            if duration and capabilities()["piper"]["ready"]:
                voice = _piper_audio(outdir, " ".join(lines))
            preview = None
            if duration and capabilities()["ffmpeg"]["ready"]:
                preview = _ffmpeg_render(outdir, art, duration, voice)
            manifest = {
                "item_id": item["id"], "job_id": job_id, "channel": item["channel_id"],
                "character": LEADS[item["channel_id"]], "topic": item["topic"],
                "content_type": item["content_type"], "target_duration_seconds": target,
                "rendered_duration_seconds": duration if preview else 0,
                "render_mode": job["mode"], "render_kind": "STATIC_CONCEPT_STORYBOARD",
                "video_created": bool(preview), "voice_created": bool(voice),
                "ai_animated": False, "music_generated": False, "published": False,
                "qa_approved": False, "status_note": "Concept vizual static, nu video AI final și nu aprobare de publicare",
                "files": [p.name for p in outdir.iterdir() if p.is_file()],
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            (outdir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            # Store absolute local directory only; no user-supplied path in the DB.
            _set_status(job_id, "DONE" if preview or item["content_type"] == "image" else "PACKAGE_ONLY",
                        result=manifest, output=str(outdir))
        except Exception as exc:
            # Do not leak environment paths/stack traces into the public UI.
            _set_status(job_id, "FAILED", error=str(exc)[:800])


def output_file(job_id: int, kind: Literal["video", "script", "subtitles", "manifest", "image", "voice"]) -> Path | None:
    names = {"video": "concept-preview.mp4", "script": "script.txt", "subtitles": "captions.srt",
             "manifest": "manifest.json", "image": "character-concept.webp", "voice": "voice.wav"}
    job = get_job(job_id)
    if not job or job["status"] not in ("DONE", "PACKAGE_ONLY") or not job["output_relpath"]:
        return None
    root = Path(os.getenv("BERRY_OUTPUT_DIR", str(OUTPUT_ROOT))).resolve()
    outdir = Path(job["output_relpath"]).resolve()
    if outdir.parent != root or outdir.name != f"job_{job_id:06d}":
        return None
    path = outdir / names[kind]
    return path if path.is_file() else None
