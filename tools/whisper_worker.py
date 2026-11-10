"""Offline faster-whisper transcription using only preinstalled local model files."""
import json
import sys
from pathlib import Path


def stamp(seconds):
    ms = max(0, round(seconds * 1000))
    return f'{ms // 3600000:02}:{(ms // 60000) % 60:02}:{(ms // 1000) % 60:02},{ms % 1000:03}'


def main():
    model_dir, audio_path, output_path = map(Path, sys.argv[1:4])
    from faster_whisper import WhisperModel
    model = WhisperModel(str(model_dir), device='cpu', compute_type='int8', local_files_only=True)
    segments, _ = model.transcribe(str(audio_path), vad_filter=True)
    lines = []
    for idx, segment in enumerate(segments, 1):
        lines.append(f'{idx}\n{stamp(segment.start)} --> {stamp(segment.end)}\n{segment.text.strip()}\n')
    output_path.write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'success': True, 'segments': len(lines)}))


if __name__ == '__main__':
    main()
