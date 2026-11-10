"""Deterministic offline motion-graphics assembly (NOT generative 3D AI).

Pillow creates reviewable title scenes using the supplied character concept art.
FFmpeg renders an actual multi-scene MP4 with subtle camera motion and optional
local Piper narration. All processing stays on the user's computer.
"""
from __future__ import annotations

import math
import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .studio import binary_path

SIZE = (360, 640)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / ("arialbd.ttf" if bold else "arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines[:6]


def _scene(art: Path, channel: str, topic: str, line: str, index: int, out: Path) -> None:
    with Image.open(art) as src:
        image = ImageOps.fit(src.convert("RGB"), SIZE, method=Image.Resampling.LANCZOS)
    image = image.convert("RGBA")
    tint = Image.new("RGBA", SIZE, (7, 12, 26, 95))
    image = Image.alpha_composite(image, tint)
    overlay = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(350, 640):
        alpha = int(220 * (y - 350) / 290)
        draw.line((0, y, 360, y), fill=(7, 9, 23, alpha))
    draw.rounded_rectangle((18, 18, 170, 48), radius=13, fill=(17, 24, 41, 220))
    draw.text((28, 26), "BERRY / " + channel.upper()[:9], font=_font(12, True), fill="white")
    draw.text((22, 360), f"SCENA {index + 1} / 4", font=_font(13, True), fill="#f8b2d5")
    y = 394
    for segment in _wrap(draw, topic, _font(25, True), 320)[:3]:
        draw.text((22, y), segment, font=_font(25, True), fill="white", stroke_width=1, stroke_fill="#1a1c2c")
        y += 34
    y = max(y + 12, 505)
    for segment in _wrap(draw, line, _font(15), 316)[:4]:
        draw.text((22, y), segment, font=_font(15), fill="#e2e8f0")
        y += 21
    draw.text((22, 610), "CONCEPT MOTION GRAPHICS • REVIZUIRE NECESARĂ", font=_font(9), fill="#d6a6bd")
    Image.alpha_composite(image, overlay).convert("RGB").save(out, "PNG", optimize=True)


def render(outdir: Path, art: Path, channel: str, topic: str, lines: list[str], duration: int,
           voice: Path | None = None, soundtrack: Path | None = None) -> tuple[Path, Path]:
    if not (ffmpeg := binary_path("ffmpeg", "BERRY_FFMPEG_PATH")):
        raise FileNotFoundError("FFmpeg nu este disponibil")
    scenes = []
    for idx in range(4):
        path = outdir / f"scene-{idx+1}.png"
        _scene(art, channel, topic, lines[idx % len(lines)], idx, path)
        scenes.append(path)
    if duration <= 0:
        return scenes[0], scenes[0]
    # Generate each segment independently to bound memory and keep progress artifacts.
    chunks = []
    for i, scene in enumerate(scenes):
        seconds = duration // 4 + (1 if i < duration % 4 else 0)
        if seconds <= 0:
            continue
        part = outdir / f"part-{i+1}.mp4"
        cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-loop", "1", "-framerate", "12",
               "-i", str(scene), "-t", str(seconds), "-vf",
               "zoompan=z='min(zoom+0.0005,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=360x640:fps=12,format=yuv420p",
               "-r", "12", "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "27", str(part)]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=max(60, seconds * 8), check=False)
        if p.returncode or not part.is_file():
            raise RuntimeError("FFmpeg segment: " + (p.stderr or "Eroare necunoscută")[-450:])
        chunks.append(part)
    listfile = outdir / "segments.ffconcat"
    # Fixed generated filenames, never paths supplied by the client.
    listfile.write_text("ffconcat version 1.0\n" + "".join(f"file '{p.name}'\n" for p in chunks), encoding="utf-8")
    video = outdir / "motion-video.mp4"
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-safe", "0", "-f", "concat", "-i", str(listfile)]
    if voice and soundtrack:
        cmd += ["-i", str(voice), "-stream_loop", "-1", "-i", str(soundtrack),
                "-filter_complex", "[1:a]apad,volume=1.0[v];[2:a]volume=0.18[m];[v][m]amix=inputs=2:duration=longest:dropout_transition=0[a]",
                "-map", "0:v:0", "-map", "[a]"]
    elif voice or soundtrack:
        audio = voice or soundtrack
        cmd += ["-stream_loop", "-1", "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-map", "0:v:0", "-map", "1:a:0"]
    cmd += ["-t", str(duration), "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(video)]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=max(90, duration * 3), check=False)
    if p.returncode or not video.is_file() or video.stat().st_size < 2000:
        raise RuntimeError("FFmpeg asamblare: " + (p.stderr or "Eroare necunoscută")[-450:])
    # Keep the finished scene PNGs; intermediates aren't needed for delivery.
    for part in chunks:
        part.unlink(missing_ok=True)
    listfile.unlink(missing_ok=True)
    return video, scenes[0]
