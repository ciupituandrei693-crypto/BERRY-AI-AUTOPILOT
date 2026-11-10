"""Opt-in local Blender rigged fruit animation with audio-driven mouth cues.

This is a procedural 3D baseline, not a diffusion-generated film. The user must
install Blender locally; Rhubarb (optional) provides phonetic mouth shapes.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

from . import studio

ROOT = Path(__file__).resolve().parents[1]
SHAPES = frozenset('ABCDEFGHX')


def _run(args: list[str], timeout: int) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('Motorul 3D a depășit timpul maxim local') from exc


def _wav_16k(audio: Path, dest: Path) -> Path:
    ffmpeg = studio.binary_path('ffmpeg', 'BERRY_FFMPEG_PATH')
    if not ffmpeg:
        raise ValueError('FFmpeg este necesar pentru sincronizarea audio')
    p = _run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(audio),
              '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(dest)], 180)
    if p.returncode or not dest.is_file():
        raise RuntimeError('Nu s-a putut converti vocea în WAV mono')
    return dest


def _validate_cues(raw: object, duration: float) -> list[dict]:
    if not isinstance(raw, list) or len(raw) > 30000:
        raise ValueError('Date Rhubarb invalide')
    result = []
    last = 0.0
    for cue in raw:
        if not isinstance(cue, dict):
            raise ValueError('Cue invalid')
        a, b, value = cue.get('start'), cue.get('end'), cue.get('value')
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)) or not isinstance(value, str):
            raise ValueError('Cue invalid')
        if not all(math.isfinite(x) for x in (a, b)) or a < last - 0.02 or b < a or value not in SHAPES:
            raise ValueError('Timp sau fonem invalid')
        if a >= duration:
            break
        result.append({'start': round(max(0.0, a), 3), 'end': round(min(duration, b), 3), 'value': value})
        last = a
    return result


def _energy_cues(wav: Path, duration: float) -> list[dict]:
    """Explicitly approximate mouth motion from energy, not phoneme alignment."""
    with wave.open(str(wav), 'rb') as f:
        if f.getnchannels() != 1 or f.getsampwidth() != 2 or f.getframerate() != 16000:
            raise ValueError('WAV trebuie să fie PCM 16kHz mono')
        frames = f.readframes(min(f.getnframes(), int(duration * 16000)))
    values = []
    hop = 1600  # 100 ms
    for off in range(0, len(frames), hop * 2):
        chunk = frames[off:off + hop * 2]
        count = len(chunk) // 2
        if not count:
            break
        samples = struct.unpack('<' + 'h' * count, chunk)
        rms = math.sqrt(sum(v*v for v in samples) / count) / 32768.0
        values.append(rms)
    if not values:
        return []
    peak = max(sorted(values)[int(len(values) * .95):] or [0.0])
    threshold = max(0.006, peak * .13)
    cues = []
    for idx, v in enumerate(values):
        value = 'X' if v < threshold else ('D' if v > peak * .5 else 'A')
        start = idx * .1
        if cues and cues[-1]['value'] == value:
            cues[-1]['end'] = round(min(duration, start + .1), 3)
        else:
            cues.append({'start': round(start, 3), 'end': round(min(duration, start + .1), 3), 'value': value})
    return cues


def mouth_cues(audio: Path | None, workdir: Path, duration: float) -> tuple[list[dict], str]:
    if not audio:
        return [], 'NO_VOICE_NO_LIPSYNC'
    wav = _wav_16k(audio, workdir / 'voice_16k.wav')
    rhubarb = studio.binary_path('rhubarb', 'BERRY_RHUBARB_PATH')
    if rhubarb:
        output = workdir / 'rhubarb.json'
        p = _run([rhubarb, '-f', 'json', '-o', str(output), str(wav)], max(120, int(duration * 5)))
        if p.returncode == 0 and output.is_file():
            try:
                cues = _validate_cues(json.loads(output.read_text(encoding='utf-8')).get('mouthCues'), duration)
                if cues:
                    return cues, 'RHUBARB_PHONETIC_LOCAL'
            except (ValueError, OSError, json.JSONDecodeError, AttributeError):
                pass
    return _energy_cues(wav, duration), 'ENERGY_APPROXIMATION_NOT_PHONEMES'


def render_item(item: dict, job_id: int) -> dict:
    blender = studio.binary_path('blender', 'BERRY_BLENDER_PATH')
    if not blender:
        raise ValueError('Blender nu este instalat sau BERRY_BLENDER_PATH nu este configurat')
    from .creative import assets_dir
    root = assets_dir()
    voice = next((p for ext in ('wav', 'mp3') if (p := root / f"item_{item['id']}_voice.{ext}").is_file()), None)
    # Short test by default; full render is a separate explicit action, not automatic.
    duration = min({'main90': 90, 'short15': 15, 'image': 6, 'longform': 300}[item['content_type']],
                   max(2, int(os.getenv('BERRY_3D_MAX_SECONDS', '6'))))
    resolution = min(720, max(180, int(os.getenv('BERRY_3D_WIDTH', '360'))))
    fps = min(24, max(8, int(os.getenv('BERRY_3D_FPS', '12'))))
    work = Path(os.getenv('BERRY_OUTPUT_DIR', str(studio.OUTPUT_ROOT))) / f'rig3d_{job_id:06d}'
    work.mkdir(parents=True, exist_ok=True)
    cues, method = mouth_cues(voice, work, duration)
    (work / 'mouth_cues.json').write_text(json.dumps(cues, ensure_ascii=False, indent=2), encoding='utf-8')
    config = {
        'channel': item['channel_id'], 'duration': duration, 'width': resolution,
        'fps': fps, 'output': str(work / 'rigged_animation.mp4'),
        'blend': str(work / 'rigged_character.blend'), 'cues': cues,
        'samples': 12,
    }
    config_path = work / 'blender_config.json'
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding='utf-8')
    script = ROOT / 'tools' / 'blender_fruit_scene.py'
    p = _run([blender, '--background', '--factory-startup', '--threads', '2',
              '--python', str(script), '--', '--config', str(config_path)],
             max(240, duration * 95))
    source = work / 'rigged_animation.mp4'
    blend = work / 'rigged_character.blend'
    if p.returncode or not source.is_file() or source.stat().st_size < 1000 or not blend.is_file():
        (work / 'blender_error.txt').write_text((p.stderr or p.stdout or 'Blender failed')[-4000:], encoding='utf-8')
        raise RuntimeError('Blender 3D nu a terminat; vezi logul local din rig3d_*')
    ffmpeg = studio.binary_path('ffmpeg', 'BERRY_FFMPEG_PATH')
    if ffmpeg:
        verify = _run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-i', str(source),
                       '-frames:v', '1', '-f', 'null', '-'], 40)
        if verify.returncode:
            raise RuntimeError('Fișierul Blender MP4 nu poate fi decodat de FFmpeg')
    target = root / f"item_{item['id']}_video.mp4"
    # Mux voice to rendered video. Never replace a working target on failure.
    final = work / 'with_voice.mp4'
    if voice:
        if not ffmpeg:
            raise ValueError('FFmpeg este necesar pentru vocea din animație')
        p = _run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
                  '-i', str(voice), '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy',
                  '-c:a', 'aac', '-af', 'apad', '-t', str(duration), '-movflags', '+faststart', str(final)],
                 max(120, duration * 3))
        if p.returncode or not final.is_file() or final.stat().st_size < 1000:
            raise RuntimeError('FFmpeg nu a putut combina vocea cu animația 3D')
    shutil.copyfile(final if voice else source, target)
    provenance = {'engine': 'BLENDER_PROCEDURAL_3D', 'lipsync_method': method,
                  'rigging': 'ARMATURE_AND_SHAPE_KEYS', 'duration_seconds': duration,
                  'filename': target.name, 'blend_project': blend.name,
                  'local_only': True, 'review_required': True, 'published': False,
                  'rendered_frames': round(duration * fps), 'fps_target': fps,
                  'render_width': resolution, 'hardware_verified': False}
    (root / f"item_{item['id']}_video_source.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding='utf-8')
    return provenance
