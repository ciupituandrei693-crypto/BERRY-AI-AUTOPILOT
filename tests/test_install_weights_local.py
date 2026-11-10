"""Offline contract tests for curated weights download helper."""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from tools import install_weights_local


def test_only_allowlisted_models(tmp_path):
    with pytest.raises(ValueError):
        install_weights_local.download_model("unknown/remote/code", tmp_path / "weights")
    assert "whisper_small" in install_weights_local.MODELS
    assert "piper_ro" in install_weights_local.MODELS


def test_local_download_mock_without_network(monkeypatch, tmp_path):
    fake = types.ModuleType("huggingface_hub")
    seen = {}

    def snapshot_download(**kwargs):
        seen.update(kwargs)
        folder = Path(kwargs["local_dir"])
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "model.bin").write_bytes(b"example")
        return str(folder)

    fake.snapshot_download = snapshot_download
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake)
    result = install_weights_local.download_model("whisper_small", tmp_path / "whisper")
    assert seen["token"] is False
    assert seen["max_workers"] == 2
    assert result["downloaded_only"] is True
    assert result["inference_tested"] is False
    assert result["files"] == 1


def test_empty_snapshot_rejected(monkeypatch, tmp_path):
    fake = types.ModuleType("huggingface_hub")
    fake.snapshot_download = lambda **kwargs: kwargs["local_dir"]
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake)
    with pytest.raises(RuntimeError):
        install_weights_local.download_model("whisper_small", tmp_path / "empty")


def test_piper_requires_voice_model(monkeypatch, tmp_path):
    fake = types.ModuleType("huggingface_hub")
    def snapshot_download(**kwargs):
        folder = Path(kwargs["local_dir"])
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "MODEL_CARD").write_text("example", encoding="utf-8")
        return str(folder)
    fake.snapshot_download = snapshot_download
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake)
    with pytest.raises(RuntimeError):
        install_weights_local.download_model("piper_ro", tmp_path / "voice")
