"""Validate and optionally import the 3 exact user-supplied ZIPs, without execution.

Default is verify-only. --extract copies sources into new local_engines folders.
Never overwrites, executes scripts, connects to a network or enables publishing.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import stat
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

SOURCES = {
    'instagram': {
        'archive': 'instagram-agent-skill-main(2).zip',
        'sha256': 'c4bd00ef53fd9c45b5c6e3f6390f3456cac290a6a84ecf1fd97177c692515518',
        'root': 'instagram-agent-skill-main', 'target': 'InstagramAgentSkill',
        'max_entries': 100, 'max_bytes': 5_000_000, 'license': 'MIT'},
    'hyperframes': {
        'archive': 'hyperframes-main(2).zip',
        'sha256': 'a216caa6a2c7260c5936adcb36895e7ddad2d80dafef3b4f439b52b816361db1',
        'root': 'hyperframes-main', 'target': 'HyperFramesSource',
        'max_entries': 13000, 'max_bytes': 400_000_000, 'license': 'Apache-2.0'},
    'openclipper': {
        'archive': 'OpenClipper-master.zip',
        'sha256': 'f9fb461401d34d9f6a20a7dedfdc66f7c7424872776ec735b8b6b303f09585ce',
        'root': 'OpenClipper-master', 'target': 'OpenClipper',
        'max_entries': 1300, 'max_bytes': 250_000_000, 'license': 'MIT'},
}
MAX_FILE = 100_000_000


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def inspect_zip(path: Path, spec: dict) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f'Arhiva lipseste: {path}')
    digest = sha256_file(path)
    if digest != spec['sha256']:
        raise ValueError('SHA256 diferit de arhiva primita si verificata; import oprit')
    with zipfile.ZipFile(path) as z:
        members = z.infolist()
        if len(members) > spec['max_entries']:
            raise ValueError('Prea multe fisiere in ZIP')
        if z.testzip() is not None:
            raise ValueError('CRC invalid in ZIP')
        total, seen, symlinks = 0, set(), []
        for member in members:
            raw = member.filename
            if ('\\' in raw or raw.startswith('/') or ':' in raw or '\x00' in raw):
                raise ValueError(f'Cale ZIP nesigura: {raw!r}')
            parts = PurePosixPath(raw).parts
            if not parts or parts[0] != spec['root'] or '..' in parts:
                raise ValueError(f'Cale in afara arhivei: {raw!r}')
            if len(parts) == 1:
                continue
            key = '/'.join(parts[1:]).lower()
            if key in seen:
                raise ValueError(f'Cale duplicata: {raw!r}')
            seen.add(key)
            if stat.S_ISLNK(member.external_attr >> 16):
                symlinks.append(raw)
                continue
            if member.flag_bits & 1:
                raise ValueError('ZIP criptat neacceptat')
            if member.file_size > MAX_FILE:
                raise ValueError(f'Fisier prea mare: {raw!r}')
            total += member.file_size
            if total > spec['max_bytes']:
                raise ValueError('Limita de decomprimare depasita')
        return {
            'archive': path.name, 'sha256': digest, 'entries': len(members),
            'unpacked_bytes_excluding_symlinks': total, 'symlinks_skipped': symlinks,
            'license': spec['license'], 'verified': True, 'code_executed': False,
        }


def import_zip(path: Path, spec: dict, destination: Path) -> dict:
    report = inspect_zip(path, spec)
    if destination.exists():
        raise FileExistsError(f'Folder existent: {destination}; nu suprascriu')
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.berry-import-', dir=destination.parent))
    try:
        with zipfile.ZipFile(path) as z:
            for member in z.infolist():
                parts = PurePosixPath(member.filename).parts
                if len(parts) <= 1 or stat.S_ISLNK(member.external_attr >> 16):
                    continue
                out = staging.joinpath(*parts[1:])
                if member.is_dir():
                    out.mkdir(parents=True, exist_ok=True)
                else:
                    out.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(member) as src, out.open('xb') as dest:
                        shutil.copyfileobj(src, dest, 1024 * 1024)
        staging.rename(destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {**report, 'source_imported': True, 'destination': str(destination),
            'inference_tested': False, 'publishing_enabled': False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip-dir', type=Path, required=True)
    parser.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--extract', action='store_true',
                        help='Import verified source files; default is verification only')
    args = parser.parse_args(argv)
    results = []
    for key, spec in SOURCES.items():
        path = args.zip_dir / spec['archive']
        dest = args.project_root / 'local_engines' / spec['target']
        try:
            result = import_zip(path, spec, dest) if args.extract else inspect_zip(path, spec)
            results.append({'component': key, 'status': 'IMPORTED' if args.extract else 'VERIFIED', **result})
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            results.append({'component': key, 'status': 'ERROR', 'error': str(exc)})
    print(json.dumps({
        'product': 'BERRY AI AUTOPILOT', 'utc': datetime.now(timezone.utc).isoformat(),
        'mode': 'EXTRACT' if args.extract else 'VERIFY_ONLY',
        'cloud_enabled': False, 'social_publishing_enabled': False,
        'scripts_executed': False, 'items': results,
    }, ensure_ascii=False, indent=2))
    return 0 if all(x['status'] != 'ERROR' for x in results) else 1


if __name__ == '__main__':
    sys.exit(main())
