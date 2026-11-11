"""BERRY Windows-local final validation and performance report (no cloud).

Run from project root:
  python tools/pc_validation.py             # quick checks + FFmpeg benchmark
  python tools/pc_validation.py --full      # also Blender real 3D render
  python tools/pc_validation.py --tests     # also pytest (if installed)
No model downloads, social logins, spending or server connections.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _step(name: str, status: str, detail: str = "", seconds: float | None = None) -> dict:
    return {"name": name, "status": status, "detail": detail[:400],
            "elapsed_seconds": round(seconds, 2) if seconds is not None else None}


def _run(argv: list[str], timeout: int, cwd: Path | None = None) -> tuple[int, float, str]:
    started = time.monotonic()
    try:
        p = subprocess.run(argv, cwd=str(cwd) if cwd else None, capture_output=True,
                           text=True, errors="replace", timeout=timeout, check=False)
        return p.returncode, time.monotonic() - started, (p.stderr or p.stdout or "")[-1500:]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, time.monotonic() - started, type(exc).__name__


def _api_smoke(tmp: Path) -> dict:
    started = time.monotonic()
    try:
        from fastapi.testclient import TestClient
        from berry import db
        from berry.app import app
        old = db.DB
        db.DB = tmp / "smoke.sqlite3"
        try:
            with TestClient(app) as client:
                status = client.get("/api/status")
                channels = client.get("/api/channels")
                created = client.post("/api/items", json={
                    "channel_id": "lab", "content_type": "short15",
                    "topic": "Verificare locală AFINA"
                })
                engines = client.get("/api/engines")
                passed = (status.status_code == 200 and channels.status_code == 200
                          and created.status_code == 201 and engines.status_code == 200
                          and len(channels.json()) == 5
                          and status.json()["external_server"] is False
                          and engines.json()["cloud"] is False)
        finally:
            db.DB = old
        return _step("API FastAPI + SQLite + 5 canale", "PASS" if passed else "FAIL",
                     "Test în bază temporară, fără publicare", time.monotonic()-started)
    except Exception as exc:
        return _step("API FastAPI + SQLite + 5 canale", "FAIL",
                     "Eroare locală: " + type(exc).__name__, time.monotonic()-started)


def _ffmpeg_benchmark(tmp: Path) -> dict:
    from berry.studio import binary_path
    exe = binary_path("ffmpeg", "BERRY_FFMPEG_PATH")
    if not exe:
        return _step("FFmpeg MP4 2s 360x640", "SKIP", "FFmpeg nu este disponibil")
    output = tmp / "benchmark_ffmpeg.mp4"
    args = [exe, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "testsrc2=size=360x640:rate=12",
            "-t", "2", "-an", "-c:v", "mpeg4", "-q:v", "5", "-pix_fmt", "yuv420p",
            str(output)]
    code, seconds, message = _run(args, 120)
    valid = code == 0 and output.is_file() and output.stat().st_size > 1000
    return _step("FFmpeg MP4 2s 360x640", "PASS" if valid else "FAIL",
                 ("Fișier valid; raport randare/timp: %.2fx" % (2/seconds if seconds else 0))
                 if valid else ("Randarea a eșuat: " + message[:200]), seconds)


def _blender_benchmark(tmp: Path) -> dict:
    from berry.studio import binary_path
    exe = binary_path("blender", "BERRY_BLENDER_PATH")
    if not exe:
        return _step("Blender 3D 2s 180px", "SKIP", "Blender nu este instalat")
    work = tmp / "blender"
    work.mkdir()
    config = {"channel": "lab", "duration": 2, "width": 180, "fps": 8,
              "output": str(work / "rigged_animation.mp4"),
              "blend": str(work / "rigged_character.blend"),
              "cues": [{"start": 0, "end": 0.5, "value": "A"},
                       {"start": 0.5, "end": 1, "value": "X"}],
              "samples": 8}
    cfg = work / "config.json"
    cfg.write_text(json.dumps(config), encoding="utf-8")
    args = [exe, "--background", "--factory-startup", "--threads", "2",
            "--python", str(ROOT / "tools" / "blender_fruit_scene.py"),
            "--", "--config", str(cfg)]
    code, seconds, message = _run(args, 900)
    mp4 = work / "rigged_animation.mp4"
    blend = work / "rigged_character.blend"
    passed = code == 0 and mp4.is_file() and mp4.stat().st_size > 1000 and blend.is_file()
    return _step("Blender 3D 2s 180px", "PASS" if passed else "FAIL",
                 ("16 cadre; %.2f cadre/s procesate; .blend + MP4" % (16/seconds if seconds else 0))
                 if passed else ("Verifică Blender/driverul video: " + message[:220]), seconds)


def _hyperframes_benchmark(tmp: Path) -> dict:
    from berry import hyperframes_bridge as hf, studio
    exe = hf.cli()
    if not exe:
        return _step('HyperFrames MP4 2s', 'SKIP',
                     'Configureaza BERRY_HYPERFRAMES_BIN; ZIP-ul sursa nu este CLI instalat')
    gsap = hf.local_gsap(exe)
    if not gsap:
        return _step('HyperFrames MP4 2s', 'FAIL',
                     'GSAP local lipseste; CDN-ul este interzis')
    art = studio.STATIC / 'lab.webp'
    if not art.is_file():
        return _step('HyperFrames MP4 2s', 'FAIL', 'Imaginea AFINA lipseste')
    work = tmp / 'hyperframes-smoke'
    work.mkdir()
    shutil.copyfile(gsap, work / 'gsap.min.js')
    composition = work / 'index.html'
    composition.write_text(hf._html({'title': 'AFINA testeaza HyperFrames',
                                      'topic': 'Test local 2 secunde', 'channel_id': 'lab'},
                                     2, art), encoding='utf-8')
    output = work / 'smoke.mp4'
    args = [exe, 'render', '-c', str(composition), '-o', str(output), '--fps', '12']
    if Path(exe).suffix.lower() in ('.js', '.mjs'):
        node = shutil.which('node')
        if not node:
            return _step('HyperFrames MP4 2s', 'FAIL', 'Node.js lipseste')
        args.insert(0, node)
    code, seconds, message = _run(args, 240, work)
    ok = code == 0 and output.is_file() and output.stat().st_size > 1024
    return _step('HyperFrames MP4 2s', 'PASS' if ok else 'FAIL',
                 'Compozitie HTML offline randata real in MP4' if ok
                 else 'Render local nereusit: ' + message[:180], seconds)


def _openclipper_benchmark() -> dict:
    from berry import openclipper_bridge as oc
    status = oc.status()
    if not status['online']:
        return _step('OpenClipper MCP local', 'SKIP',
                     'Aplicatia OpenClipper desktop nu ruleaza sau MCP nu este pornit')
    started = time.monotonic()
    try:
        result = oc.list_local('list_projects')
        ok = result['read_only'] and result['source'] == 'OPENCLIPPER_LOCAL_MCP'
        return _step('OpenClipper MCP local', 'PASS' if ok else 'FAIL',
                     'Listare proiecte prin MCP fara modificari',
                     time.monotonic() - started)
    except oc.OpenClipperError as exc:
        return _step('OpenClipper MCP local', 'FAIL', str(exc)[:180],
                     time.monotonic() - started)


def _jarvis_smoke(tmp: Path) -> dict:
    key = os.getenv('BERRY_JARVIS_API_KEY', '')
    if len(key) < 32:
        return _step('JARVIS ONE API local', 'SKIP',
                     'Configureaza BERRY_JARVIS_API_KEY de minimum 32 caractere')
    from fastapi.testclient import TestClient
    from berry import db
    from berry.app import app
    old = db.DB
    db.DB = tmp / 'jarvis-smoke.sqlite3'
    try:
        with TestClient(app) as client:
            r = client.get('/api/v1/jarvis/capabilities', headers={'X-JARVIS-KEY': key})
            ok = r.status_code == 200 and r.json()['social_publishing'] is False
        return _step('JARVIS ONE API local', 'PASS' if ok else 'FAIL',
                     'Cheie separata validata, publicarea blocata')
    except Exception as exc:
        return _step('JARVIS ONE API local', 'FAIL', type(exc).__name__)
    finally:
        db.DB = old


def _afina_end_to_end() -> dict:
    from berry.studio import binary_path
    if not binary_path('ffmpeg', 'BERRY_FFMPEG_PATH'):
        return _step('AFINA 15s end-to-end', 'SKIP', 'FFmpeg lipseste')
    code, seconds, message = _run([sys.executable, str(ROOT / 'tools' / 'smoke_afina.py')],
                                  280, ROOT)
    try:
        result = json.loads(message.strip())
    except (ValueError, TypeError):
        result = {}
    # The isolated smoke script exits 0 only after validating the MP4 and manifest.
    passed = code == 0 and (result.get('status') in ('PASS', None))
    return _step('AFINA 15s end-to-end', 'PASS' if passed else 'FAIL',
                 'MP4 local 15s produs in baza temporara; nepublicat' if passed
                 else 'Test AFINA nereusit: ' + message[-200:], seconds)


def _exe_smoke() -> dict:
    exe = ROOT / "dist" / "BERRY_AI_AUTOPILOT" / "BERRY_AI_AUTOPILOT.exe"
    if os.name != "nt":
        return _step("Windows EXE", "SKIP", "Testul .exe se rulează pe Windows")
    if not exe.is_file():
        return _step("Windows EXE", "SKIP", "Rulează BUILD_WINDOWS_EXE.cmd înainte")
    code, seconds, message = _run([str(exe), "--self-test"], 90)
    try:
        obj = json.loads(message) if code == 0 else {}
    except (ValueError, TypeError):
        obj = {}
    # The self-test's exit code is the authoritative success condition.
    return _step("Windows EXE", "PASS" if code == 0 else "FAIL",
                 "Self-test executabil local" if code == 0 else "Self-test executabil a eșuat",
                 seconds)


def _pytest() -> dict:
    code, seconds, message = _run([sys.executable, "-m", "pytest", "-q"], 300, ROOT)
    if "No module named pytest" in message:
        return _step("Testele automate pytest", "SKIP", "Instalează requirements-dev.txt", seconds)
    return _step("Testele automate pytest", "PASS" if code == 0 else "FAIL",
                 message[-300:], seconds)



def _recommendations(system: dict, steps: list[dict]) -> list[str]:
    advice = ["Păstrează un singur job AI activ și revizuirea umană înainte de export.",
              "Începe cu 180-360px, 8-12 FPS și randări de 2-6 secunde pentru Blender."]
    gpus = system.get("system", {}).get("gpus", [])
    names = " ".join(str(x.get("name", "")) for x in gpus).lower()
    if "radeon" in names or "amd" in names:
        advice.append("GPU AMD detectat: verifică suportul exact al fiecărui model; multe pipeline-uri CUDA necesită NVIDIA.")
    if any(x["name"].startswith("Blender") and x["status"] == "FAIL" for x in steps):
        advice.append("Blender a eșuat: verifică versiunea Blender, driverul GPU și rulează inițial cu rezoluție mică.")
    if any(x["name"].startswith("Windows EXE") and x["status"] == "SKIP" for x in steps):
        advice.append("Executabilul Windows nu a fost testat; rulează BUILD_WINDOWS_EXE.cmd și repetă validarea.")
    free = system.get("system", {}).get("disk_free_gib")
    if isinstance(free, (int, float)) and free < 20:
        advice.append("Sub 20 GiB liberi: eliberează spațiu înainte de instalarea checkpoints mari.")
    advice.append("Nu activa server extern, GPU cloud sau publicare automată înainte de aprobarea separată.")
    return advice


def validate(full: bool = False, tests: bool = False) -> dict:
    from berry import diagnostics, model_bridge
    report = {"product": "BERRY AI AUTOPILOT", "phase": "LOCAL_STAGES_1_TO_11",
              "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "machine": platform.node()[:80], "local_only": True,
              "external_server_connected": False, "cloud_gpu_used": False,
              "social_publishing_enabled": False,
              "system": diagnostics.report(), "steps": []}
    with tempfile.TemporaryDirectory(prefix="berry-validation-") as folder:
        tmp = Path(folder)
        report["steps"].append(_api_smoke(tmp))
        report["steps"].append(_ffmpeg_benchmark(tmp))
        if full:
            report["steps"].append(_blender_benchmark(tmp))
        else:
            report["steps"].append(_step("Blender 3D 2s 180px", "SKIP",
                                          "Rulează cu --full pentru benchmark real"))
        if full:
            report["steps"].append(_hyperframes_benchmark(tmp))
            report["steps"].append(_openclipper_benchmark())
            report["steps"].append(_afina_end_to_end())
        else:
            report["steps"].append(_step('HyperFrames MP4 2s', 'SKIP', 'Ruleaza cu --full'))
            report["steps"].append(_step('OpenClipper MCP local', 'SKIP', 'Ruleaza cu --full'))
            report["steps"].append(_step('AFINA 15s end-to-end', 'SKIP', 'Ruleaza cu --full'))
        report["steps"].append(_jarvis_smoke(tmp))
        report["steps"].append(_exe_smoke())
        if tests:
            report["steps"].append(_pytest())
    report["model_bridges"] = {name: model_bridge.status(name) for name in model_bridge.KINDS}
    report["optimization_recommendations"] = _recommendations(report["system"], report["steps"])
    report["counts"] = {s: sum(x["status"] == s for x in report["steps"])
                        for s in ("PASS", "FAIL", "SKIP")}
    report["local_media_benchmark_completed"] = any(x["name"].startswith(("FFmpeg", "Blender")) and x["status"] == "PASS" for x in report["steps"])
    report["blender_3d_benchmarked"] = any(x["name"].startswith("Blender") and x["status"] == "PASS" for x in report["steps"])
    report["ai_model_inference_benchmarked"] = False
    report["all_selected_tests_passed"] = report["counts"]["FAIL"] == 0
    report["ready_for_external_phase"] = False
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="BERRY - teste PC și optimizare LOCALĂ")
    parser.add_argument("--full", action="store_true", help="Rulează și Blender real 3D")
    parser.add_argument("--tests", action="store_true", help="Rulează și pytest")
    args = parser.parse_args()
    try:
        report = validate(full=args.full, tests=args.tests)
    except Exception as exc:
        print("BERRY VALIDATION FAILED: " + type(exc).__name__, file=sys.stderr)
        return 2
    out = Path(os.getenv("LOCALAPPDATA") or Path.home()) / "BERRY_AI_AUTOPILOT" / "reports"
    out.mkdir(parents=True, exist_ok=True)
    dest = out / ("pc_validation_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json")
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("BERRY LOCAL PC VALIDATION")
    for step in report["steps"]:
        print("[%s] %s — %s" % (step["status"], step["name"], step["detail"]))
    print("Raport JSON: " + str(dest))
    print("Nicio conectare la server extern, GPU cloud sau rețele sociale.")
    return 1 if report["counts"]["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
