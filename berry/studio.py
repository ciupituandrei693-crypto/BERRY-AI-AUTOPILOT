"""BERRY local-first media assembly v0.2.

Generates reviewable storyboard assets and, if FFmpeg is installed, a *static
concept preview* (NOT AI video). Does not download, post, spend, or use cloud.
"""
from __future__ import annotations

import json
import os
import re
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
    found = shutil.which(name)
    if found:
        return found
    if name == "ffmpeg":
        try:
            import imageio_ffmpeg
            exe = Path(imageio_ffmpeg.get_ffmpeg_exe())
            return str(exe) if exe.is_file() else None
        except (ImportError, RuntimeError, OSError):
            return None
    return None


def capabilities() -> dict:
    ffmpeg = binary_path("ffmpeg", "BERRY_FFMPEG_PATH")
    piper = binary_path("piper", "BERRY_PIPER_PATH")
    model = Path(os.getenv("BERRY_PIPER_MODEL", "")).expanduser() if os.getenv("BERRY_PIPER_MODEL") else None
    return {
        "ffmpeg": {"ready": bool(ffmpeg), "detail": "Randare locală MP4" if ffmpeg else "Instalează FFmpeg sau configurează BERRY_FFMPEG_PATH"},
        "piper": {"ready": bool(piper and model and model.is_file()), "detail": "TTS local, dacă vocea .onnx este configurată"},
        "windows_sapi": {"ready": os.name == "nt", "detail": "Voce offline Windows inclusă în sistem; calitatea depinde de vocile instalate"},
        "koboldcpp": {"ready": False, "detail": "Adaptor disponibil; modelul local trebuie pornit separat"},
        "blender": {"ready": bool(binary_path("blender", "BERRY_BLENDER_PATH")), "detail": "Rig 3D procedural integrat; Blender trebuie instalat și testat local"},
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
    script_root = Path(os.getenv("BERRY_SCRIPT_DIR", str(ROOT / "data" / "scripts")))
    custom = script_root / f"item_{item['id']}.txt"
    if custom.is_file():
        return [line.strip() for line in custom.read_text(encoding="utf-8").splitlines() if line.strip()]
    topic = " ".join(item["topic"].split())
    lead = LEADS[item["channel_id"]]
    opening = [
        f"{lead} prezintă: {topic}.",
        f"Astăzi vorbim despre {topic} și încercăm să înțelegem de ce contează.",
        "Pornim de la o întrebare simplă: ce știm sigur și ce trebuie verificat?",
        "Mai întâi, definim termenii și evităm concluziile grăbite.",
        "Apoi analizăm un exemplu concret, din viața de zi cu zi.",
        "Ce informație ne-ar ajuta să înțelegem mai bine această situație?",
        "Privim subiectul și dintr-o a doua perspectivă, fără exagerări.",
        "Atenție la diferența dintre o opinie și un fapt verificabil.",
        "O explicație bună are surse clare și recunoaște incertitudinea.",
        "Dacă aplicăm această idee, ce se schimbă în felul în care decidem?",
        "Înainte să încheiem, recapitulăm întrebările importante.",
        f"Aceasta a fost perspectiva lui {lead} asupra subiectului {topic}.",
        "Ce întrebare ai vrea să explorăm în episodul următor?",
    ]
    if item["content_type"] == "short15":
        return [opening[0], opening[2], opening[-1]]
    if item["content_type"] == "longform":
        return opening + [f"Capitolul {i+1}: revenim la tema {topic}. " + opening[(i+3)%len(opening)] for i in range(24)]
    return opening


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


def _windows_sapi_audio(outdir: Path, text: str) -> Path | None:
    """Optional offline fallback using built-in Windows speech; never a voice clone."""
    if os.name != "nt" or os.getenv("BERRY_SAPI_TTS", "true").lower() != "true":
        return None
    ps = shutil.which("powershell.exe")
    if not ps:
        return None
    script = outdir / "local_sapi.ps1"
    input_text = outdir / "voice_input.txt"
    output = outdir / "voice.wav"
    input_text.write_text(text, encoding="utf-8-sig")
    script.write_text("param([string]$TextFile, [string]$WaveFile)\n"
        "Add-Type -AssemblyName System.Speech\n"
        "$voice = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
        "try {\n"
        "  $voice.SetOutputToWaveFile($WaveFile)\n"
        "  $voice.Speak([System.IO.File]::ReadAllText($TextFile, [System.Text.Encoding]::UTF8))\n"
        "} finally { $voice.Dispose() }\n", encoding="utf-8")
    try:
        p = subprocess.run([ps, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                            str(script), str(input_text), str(output)], capture_output=True, timeout=180, check=False)
        if p.returncode == 0 and output.is_file() and output.stat().st_size > 1000:
            return output
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


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


def _video_seconds(video: Path) -> float | None:
    ffmpeg = binary_path("ffmpeg", "BERRY_FFMPEG_PATH")
    if not ffmpeg:
        return None
    try:
        result = subprocess.run([ffmpeg, "-hide_banner", "-i", str(video)],
                                capture_output=True, text=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not match:
        return None
    h, m, sec = match.groups()
    return round(int(h) * 3600 + int(m) * 60 + float(sec), 2)


def _mux_imported_video(source: Path, outdir: Path, voice: Path | None, soundtrack: Path | None) -> Path:
    dest = outdir / "final-video.mp4"
    if not (voice or soundtrack):
        shutil.copyfile(source, dest)
        return dest
    ffmpeg = binary_path("ffmpeg", "BERRY_FFMPEG_PATH")
    if not ffmpeg:
        raise RuntimeError("FFmpeg este necesar pentru combinarea video + audio")
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source)]
    if voice and soundtrack:
        cmd += ["-i", str(voice), "-stream_loop", "-1", "-i", str(soundtrack),
                "-filter_complex", "[1:a]apad[v];[2:a]volume=0.18[m];[v][m]amix=inputs=2:duration=longest[a]",
                "-map", "0:v:0", "-map", "[a]"]
    else:
        cmd += ["-stream_loop", "-1", "-i", str(voice or soundtrack), "-map", "0:v:0", "-map", "1:a:0"]
    cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(dest)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, check=False)
    if result.returncode or not dest.is_file():
        raise RuntimeError("FFmpeg nu a putut combina video cu audio")
    return dest


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
            asset_root = Path(os.getenv("BERRY_ASSET_DIR", str(ROOT / "data" / "assets")))
            user_art = asset_root / f"item_{item['id']}.webp"
            art = user_art if user_art.is_file() else STATIC / CHARACTER_ART[item["channel_id"]]
            if not art.is_file():
                raise FileNotFoundError("Imaginea concept a personajului lipsește")
            lines = _script_lines(item)
            target = {"main90": 90, "short15": 15, "image": 0, "longform": 300}[item["content_type"]]
            duration = min(target, max(2, min(15, int(os.getenv("BERRY_PREVIEW_MAX_SECONDS", "8"))))) if job["mode"] == "preview" else target
            (outdir / "script.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
            shutil.copyfile(art, outdir / "character-concept.webp")
            if duration:
                transcript = asset_root / f"item_{item['id']}_captions.srt"
                if transcript.is_file():
                    shutil.copyfile(transcript, outdir / "captions.srt")
                else:
                    (outdir / "captions.srt").write_text(_srt(lines, duration), encoding="utf-8")
            supplied = [p for p in asset_root.glob(f"item_{item['id']}_soundtrack.*") if p.suffix.lower() in ('.wav', '.mp3')]
            supplied.sort()
            soundtrack = None
            music_supplied = bool(supplied)
            if supplied:
                soundtrack = outdir / supplied[0].name
                shutil.copyfile(supplied[0], soundtrack)
            voice_source = next((p for ext in ('wav', 'mp3') if
                                 (p := asset_root / f"item_{item['id']}_voice.{ext}").is_file()), None)
            voice = None
            if voice_source:
                voice = outdir / f"voice{voice_source.suffix}"
                shutil.copyfile(voice_source, voice)
            elif duration and capabilities()["piper"]["ready"]:
                voice = _piper_audio(outdir, " ".join(lines))
            elif duration:
                voice = _windows_sapi_audio(outdir, " ".join(lines))
            preview = None
            image_path = outdir / "final-image.png"
            render_kind = "STATIC_CONCEPT_STORYBOARD"
            generated_video = asset_root / f"item_{item['id']}_video.mp4"
            if job["mode"] == "full":
                from . import motion
                motion._scene(art, item["channel_id"], item["topic"], lines[0], 0, image_path)
                if duration and generated_video.is_file():
                    preview = _mux_imported_video(generated_video, outdir, voice, soundtrack)
                    render_kind = "IMPORTED_OR_GENERATED_LOCAL_VIDEO"
                elif duration and capabilities()["ffmpeg"]["ready"]:
                    preview, _ = motion.render(outdir, art, item["channel_id"], item["topic"], lines, duration, voice, soundtrack)
                    render_kind = "MOTION_GRAPHICS_LOCAL"
                elif item["content_type"] == "image" and user_art.is_file():
                    render_kind = "IMAGE_LOCAL_IMPORTED_OR_GENERATED"
            else:
                if duration and capabilities()["ffmpeg"]["ready"]:
                    preview = _ffmpeg_render(outdir, art, duration, voice)
            manifest = {
                "item_id": item["id"], "job_id": job_id, "channel": item["channel_id"],
                "character": LEADS[item["channel_id"]], "topic": item["topic"],
                "content_type": item["content_type"], "target_duration_seconds": target,
                "rendered_duration_seconds": (_video_seconds(preview) if render_kind == "IMPORTED_OR_GENERATED_LOCAL_VIDEO" else duration) if preview else 0,
                "render_mode": job["mode"], "render_kind": render_kind,
                "video_created": bool(preview), "image_created": image_path.is_file() or art.is_file(),
                "voice_created": bool(voice), "music_supplied": music_supplied,
                "art_source": ("COMFYUI_LOCAL" if (asset_root / f"item_{item['id']}_art_source.json").is_file() else "USER_SUPPLIED") if user_art.is_file() else "BUNDLED_CONCEPT",
                "audio_source": "VOICE_AND_MUSIC" if voice and soundtrack else "VOICE" if voice else "MUSIC" if soundtrack else "SILENCE",
                "ai_animated": bool((asset_root / f"item_{item['id']}_video_source.json").is_file() and generated_video.is_file()),
                "music_generated": bool((asset_root / f"item_{item['id']}_music_source.json").is_file() and music_supplied),
                "published": False, "qa_approved": False,
                "status_note": ("Video MP4 local importat/generat; verifică proveniența și drepturile, NEPUBLICAT" if render_kind == "IMPORTED_OR_GENERATED_LOCAL_VIDEO"
                                else "Video motion graphics local, NU animație 3D AI și NU publicat" if render_kind == "MOTION_GRAPHICS_LOCAL"
                                else "Concept/imagine locală, fără publicare"),
                "files": [p.name for p in outdir.iterdir() if p.is_file()] + ["manifest.json"],
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
             "manifest": "manifest.json", "image": "character-concept.webp", "voice": "voice.wav", "soundtrack": "soundtrack.wav"}
    job = get_job(job_id)
    if not job or job["status"] not in ("DONE", "PACKAGE_ONLY") or not job["output_relpath"]:
        return None
    root = Path(os.getenv("BERRY_OUTPUT_DIR", str(OUTPUT_ROOT))).resolve()
    outdir = Path(job["output_relpath"]).resolve()
    if outdir.parent != root or outdir.name != f"job_{job_id:06d}":
        return None
    if kind == "soundtrack":
        found = list(outdir.glob(f"item_{job['item_id']}_soundtrack.*"))
        return found[0] if found else None
    if kind == "video" and (outdir / "final-video.mp4").is_file():
        return outdir / "final-video.mp4"
    if kind == "video" and (outdir / "motion-video.mp4").is_file():
        return outdir / "motion-video.mp4"
    if kind == "voice" and (outdir / "voice.mp3").is_file():
        return outdir / "voice.mp3"
    if kind == "image" and (outdir / "final-image.png").is_file():
        return outdir / "final-image.png"
    path = outdir / names[kind]
    return path if path.is_file() else None
