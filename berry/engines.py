"""Local engine discovery and guarded HTTP helpers; no cloud fallback or auto-downloads."""
from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from .studio import binary_path


class EngineError(RuntimeError):
    pass


ENDPOINTS = {
    "comfyui": ("BERRY_COMFYUI_URL", "http://127.0.0.1:8188", "/system_stats"),
    "ace_step": ("BERRY_ACE_STEP_URL", "http://127.0.0.1:8001", "/health"),
    "koboldcpp": ("BERRY_KOBOLD_URL", "http://127.0.0.1:5001", "/api/v1/model"),
    "voice_studio": ("BERRY_VOICESTUDIO_URL", "http://127.0.0.1:3900", "/health"),
}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise EngineError("Redirecționarea către altă adresă este interzisă")


OPENER = urllib.request.build_opener(_NoRedirect)


def local_base(engine: str) -> str:
    env, default, _ = ENDPOINTS[engine]
    raw = os.environ.get(env, default).strip().rstrip("/")
    parsed = urlparse(raw)
    if (parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost", "::1")
            or parsed.username or parsed.password or parsed.path not in ("", "/")
            or parsed.query or parsed.fragment or not parsed.port or not 1 <= parsed.port <= 65535):
        raise EngineError(f"{env} trebuie să fie http://127.0.0.1:PORT (fără cale sau domeniu extern)")
    return raw


def request(engine: str, path: str, *, payload: dict | None = None, timeout: int = 15,
            max_bytes: int = 2_000_000) -> bytes:
    if not path.startswith("/") or path.startswith("//") or "\\" in path:
        raise EngineError("Cale locală invalidă")
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(local_base(engine) + path, data=data,
                                 headers={"Content-Type": "application/json"} if data else {},
                                 method="POST" if data is not None else "GET")
    try:
        with OPENER.open(req, timeout=timeout) as response:
            if response.status >= 400:
                raise EngineError(f"Motorul local a returnat HTTP {response.status}")
            declared = int(response.headers.get("Content-Length", "0") or 0)
            if declared > max_bytes:
                raise EngineError("Fișierul returnat depășește limita")
            result = response.read(max_bytes + 1)
            if len(result) > max_bytes:
                raise EngineError("Fișierul returnat depășește limita")
            return result
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as exc:
        raise EngineError(f"Motorul {engine} nu răspunde local: {type(exc).__name__}") from exc


def json_request(engine: str, path: str, *, payload: dict | None = None, timeout: int = 15) -> dict:
    try:
        obj = json.loads(request(engine, path, payload=payload, timeout=timeout))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EngineError(f"Răspuns JSON invalid de la {engine}") from exc
    if not isinstance(obj, dict):
        raise EngineError(f"Format neașteptat de la {engine}")
    return obj


def _local_file(env: str) -> bool:
    v = os.environ.get(env, "").strip()
    return bool(v and Path(v).expanduser().is_file())


def _local_dir(env: str) -> bool:
    v = os.environ.get(env, "").strip()
    return bool(v and Path(v).expanduser().is_dir())


def statuses() -> dict:
    result = {}
    for engine, (env, default, path) in ENDPOINTS.items():
        configured = bool(os.environ.get(env, "").strip())
        try:
            base = local_base(engine)
            # Do not make unsolicited probes to arbitrary ports; only known local addresses.
            json_request(engine, path, timeout=2)
            online = True
            detail = "Motorul răspunde local"
        except (EngineError, OSError, ValueError) as exc:
            online = False
            detail = str(exc)[:160]
        ready = online
        if engine == "comfyui" and not _local_file("BERRY_COMFYUI_WORKFLOW"):
            ready = False
            detail = "Configurează BERRY_COMFYUI_WORKFLOW cu un workflow API JSON exportat"
        result[engine] = {"configured": configured, "online": online, "ready": ready,
                          "endpoint": base if online else default, "detail": detail,
                          "requires_local_models": True}
    wangp = _local_dir("BERRY_WANGP_ROOT") and _local_file("BERRY_WANGP_SETTINGS") and _local_file("BERRY_WANGP_PYTHON")
    result["wangp"] = {"configured": wangp, "online": False, "ready": wangp,
                       "detail": "WanGP API in-process, pornit numai la cerere; necesită modele și Python separat"}
    result["faster_whisper"] = {"configured": _local_dir("BERRY_WHISPER_MODEL"), "online": False,
                                "ready": _local_dir("BERRY_WHISPER_MODEL") and _local_file("BERRY_WHISPER_PYTHON"),
                                "detail": "Model local + Python cu faster-whisper (fără descărcări automate)"}
    from . import model_bridge
    for engine in model_bridge.KINDS:
        result[engine] = model_bridge.status(engine)
    chatterbox_source = _local_dir("BERRY_CHATTERBOX_ROOT")
    chatterbox_python = _local_file("BERRY_CHATTERBOX_PYTHON")
    result["chatterbox"] = {"configured": chatterbox_source and chatterbox_python, "online": False,
                            "ready": False, "detail": "Python TTS separat instalabil; inferența vocală rămâne de testat"}
    from . import hyperframes_bridge, openclipper_bridge
    hf = hyperframes_bridge.status()
    result["hyperframes"] = {
        "configured": hf["cli_configured"], "online": False,
        "ready": hf["ready_for_local_render"],
        "detail": "CLI + GSAP local pregatite; randarea reala trebuie validata pe Windows"
                  if hf["ready_for_local_render"] else "Configureaza CLI si GSAP local, fara CDN"}
    root = Path(__file__).resolve().parents[1]
    result["hyperframes_source"] = {
        "configured": (root / "local_engines" / "HyperFramesSource" / "package.json").is_file(),
        "online": False, "ready": False,
        "detail": "Sursa arhivei prezenta; pentru randare trebuie CLI npm separat si test MP4"}
    oc = openclipper_bridge.status()
    result["openclipper"] = {
        "configured": _local_dir("BERRY_OPENCLIPPER_ROOT") or
                      (root / "local_engines" / "OpenClipper" / "package.json").is_file(),
        "online": oc["online"], "ready": oc["online"],
        "detail": "MCP desktop local online, doar citire" if oc["online"]
                  else "Porneste OpenClipper desktop pentru MCP; exportul nu este testat"}
    from . import instagram_skill_tools
    try:
        for kind in instagram_skill_tools.SCRIPTS:
            instagram_skill_tools.checked_script(kind)
        ig_ready = True
    except instagram_skill_tools.InstagramToolError:
        ig_ready = False
    result["instagram_agent_skill"] = {
        "configured": instagram_skill_tools.source_root().is_dir(),
        "online": False, "ready": ig_ready,
        "detail": "3 verificari SEO locale disponibile; NU conecteaza Instagram si NU publica" if ig_ready
                  else "Importa ZIP-ul verificat pentru hook/caption/beat sheet"}
    result["blender"] = {"configured": bool(binary_path("blender", "BERRY_BLENDER_PATH")), "online": False,
                         "ready": bool(binary_path("blender", "BERRY_BLENDER_PATH")),
                         "detail": "Executabil Blender disponibil; script procedural 3D opțional"}
    result["rhubarb"] = {"configured": bool(binary_path("rhubarb", "BERRY_RHUBARB_PATH")),
                          "online": False, "ready": bool(binary_path("rhubarb", "BERRY_RHUBARB_PATH")),
                          "detail": "Sincronizare fonetică locală A-H dacă Rhubarb este instalat; altfel doar energie aproximativă"}
    result["blender_3d"] = {"configured": bool(binary_path("blender", "BERRY_BLENDER_PATH")),
                            "online": False, "ready": bool(binary_path("blender", "BERRY_BLENDER_PATH")),
                            "detail": "Rig 3D procedural + shape keys; testul de randare reală trebuie rulat local"}
    result["piper"] = {"configured": _local_file("BERRY_PIPER_MODEL"), "online": False,
                       "ready": bool(binary_path("piper", "BERRY_PIPER_PATH") and _local_file("BERRY_PIPER_MODEL")),
                       "detail": "Voce TTS locală cu model ONNX"}
    result["external_server"] = {"configured": False, "online": False, "ready": False,
                                 "detail": "DEZACTIVAT până la ultima etapă"}
    result["cloud_gpu"] = {"configured": False, "online": False, "ready": False,
                           "detail": "DEZACTIVAT; nu există cheltuieli"}
    result["social_publishing"] = {"configured": False, "online": False, "ready": False,
                                   "detail": "DEZACTIVAT; export manual și aprobări obligatorii"}
    return result
