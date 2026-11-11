"""Tests for offline import of user-supplied ZIPs; no original archives needed."""
import hashlib
import stat
import zipfile

import pytest

from tools import import_user_archives as importer


def make_zip(tmp_path, members):
    path = tmp_path / 'archive.zip'
    with zipfile.ZipFile(path, 'w') as z:
        for name, data in members.items():
            z.writestr(name, data)
    return path


def spec(path):
    return {'root': 'test-root', 'sha256': importer.sha256_file(path),
            'max_entries': 50, 'max_bytes': 100000,
            'license': 'MIT'}


def test_valid_archive_is_verified_without_executing(tmp_path):
    archive = make_zip(tmp_path, {'test-root/LICENSE': 'MIT', 'test-root/script.py': 'print("not executed")'})
    report = importer.inspect_zip(archive, spec(archive))
    assert report['verified'] is True
    assert report['code_executed'] is False
    assert report['entries'] == 2


def test_extract_and_refuse_overwrite(tmp_path):
    archive = make_zip(tmp_path, {'test-root/skills/tool.py': 'print("not executed")'})
    destination = tmp_path / 'local_engines' / 'InstagramAgentSkill'
    result = importer.import_zip(archive, spec(archive), destination)
    assert result['source_imported'] is True
    assert (destination / 'skills' / 'tool.py').is_file()
    assert result['inference_tested'] is False
    with pytest.raises(FileExistsError):
        importer.import_zip(archive, spec(archive), destination)


@pytest.mark.parametrize('name', [
    '../outside.txt', 'test-root/../../outside.txt', '/test-root/abs.txt',
    'test-root/../outside.txt', 'test-root/C:\\Windows\\evil.txt',
])
def test_traversal_and_windows_unsafe_paths_rejected(tmp_path, name):
    archive = make_zip(tmp_path, {name: 'evil'})
    with pytest.raises(ValueError):
        importer.inspect_zip(archive, spec(archive))


def test_wrong_sha_rejected(tmp_path):
    archive = make_zip(tmp_path, {'test-root/a': 'ok'})
    wrong = spec(archive)
    wrong['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='SHA256'):
        importer.inspect_zip(archive, wrong)


def test_symlink_skipped(tmp_path):
    archive = tmp_path / 'archive.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        info = zipfile.ZipInfo('test-root/link')
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        z.writestr(info, '../outside')
        z.writestr('test-root/readme.txt', 'hello')
    destination = tmp_path / 'out'
    result = importer.import_zip(archive, spec(archive), destination)
    assert result['symlinks_skipped'] == ['test-root/link']
    assert not (destination / 'link').exists()
    assert (destination / 'readme.txt').read_text() == 'hello'
