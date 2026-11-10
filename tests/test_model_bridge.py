"""Contract tests for opt-in LOCAL model bridge. Never start actual models."""
import json
from pathlib import Path
from subprocess import CompletedProcess

import pytest

from berry import model_bridge


def make_config(tmp_path, monkeypatch, engine="latentsync", argv=None):
    root = tmp_path / "engine"
    root.mkdir(exist_ok=True)
    python = tmp_path / "python.exe"
    python.write_bytes(b"local-python")
    (root / "inference.py").write_text("print('not executed')", encoding="utf-8")
    weights = root / "checkpoints"
    weights.mkdir(exist_ok=True)
    (weights / "model.pt").write_bytes(b"fake weights")
    config = tmp_path / "bridge.json"
    config.write_text(json.dumps({"engines": {engine: {
        "root": str(root), "python": str(python),
        "argv": argv or ["inference.py", "--video", "{video}", "--voice", "{voice}",
                          "--out", "{output}"],
        "weights": ["checkpoints/model.pt"]
    }}}), encoding="utf-8")
    monkeypatch.setenv("BERRY_MODEL_BRIDGE_CONFIG", str(config))
    return root


def test_bridge_requires_explicit_configuration(monkeypatch):
    monkeypatch.delenv("BERRY_MODEL_BRIDGE_CONFIG", raising=False)
    assert model_bridge.status("musetalk")["ready"] is False
    with pytest.raises(model_bridge.BridgeError):
        model_bridge._validate("musetalk")


def test_bridge_rejects_shell_and_remote(monkeypatch, tmp_path):
    make_config(tmp_path, monkeypatch, argv=["-c", "print(1)", "{output}"])
    assert model_bridge.status("latentsync")["ready"] is False
    make_config(tmp_path, monkeypatch, argv=["inference.py", "https://example.com", "{output}"])
    assert model_bridge.status("latentsync")["ready"] is False


def test_bridge_requires_local_weights(monkeypatch, tmp_path):
    root = make_config(tmp_path, monkeypatch)
    assert model_bridge.status("latentsync")["ready"] is True
    (root / "checkpoints" / "model.pt").unlink()
    assert model_bridge.status("latentsync")["ready"] is False


def test_bridge_runs_explicit_local_command_and_stores_mp4(monkeypatch, tmp_path):
    make_config(tmp_path, monkeypatch)
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "item_7_video.mp4").write_bytes(b"V" * 2048)
    (assets / "item_7_voice.wav").write_bytes(b"W" * 2048)
    monkeypatch.setenv("BERRY_ASSET_DIR", str(assets))
    monkeypatch.setenv("BERRY_OUTPUT_DIR", str(tmp_path / "output"))
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        assert kwargs["env"]["HF_HUB_OFFLINE"] == "1"
        assert kwargs["env"]["TRANSFORMERS_OFFLINE"] == "1"
        assert kwargs["check"] is False
        output = Path(argv[-1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"FAKE-MP4" * 300)
        return CompletedProcess(argv, 0, "finished", "")

    monkeypatch.setattr(model_bridge.subprocess, "run", fake_run)
    result = model_bridge.run("latentsync", {"id": 7}, 2)
    assert result["kind"] == "video" and result["published"] is False
    assert (assets / "item_7_video.mp4").stat().st_size > 1000
    assert len(calls) == 1
    assert model_bridge.status("latentsync")["ready"] is True


def test_bridge_needs_inputs_before_execution(monkeypatch, tmp_path):
    make_config(tmp_path, monkeypatch)
    monkeypatch.setenv("BERRY_ASSET_DIR", str(tmp_path / "missing"))
    with pytest.raises(model_bridge.BridgeError):
        model_bridge.run("latentsync", {"id": 1}, 9)
