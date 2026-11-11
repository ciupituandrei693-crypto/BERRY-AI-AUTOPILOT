"""Status checks for optional BERRY media add-ons; no network or inference."""
from __future__ import annotations

from berry import engines, openclipper_bridge


def test_addons_disabled_by_default(monkeypatch):
    for name in ("BERRY_CHATTERBOX_ROOT", "BERRY_CHATTERBOX_PYTHON",
                 "BERRY_HYPERFRAMES_BIN", "BERRY_OPENCLIPPER_ROOT",
                 "BERRY_INSTAGRAM_SKILL_ROOT"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(engines, "json_request", lambda *a, **kw: (_ for _ in ()).throw(engines.EngineError("offline")))
    monkeypatch.setattr(openclipper_bridge, "status", lambda: {"online": False})
    statuses = engines.statuses()
    for name in ("chatterbox", "hyperframes", "openclipper", "instagram_agent_skill"):
        assert statuses[name]["configured"] is False
        assert statuses[name]["ready"] is False
    assert statuses["social_publishing"]["ready"] is False


def test_local_source_presence_does_not_mean_ready(monkeypatch, tmp_path):
    chatterbox = tmp_path / "Chatterbox"
    chatterbox.mkdir()
    python = chatterbox / "python.exe"
    python.write_bytes(b"dummy")
    hyperframes = tmp_path / "hyperframes.cmd"
    hyperframes.write_text("@echo off\n")
    openclipper = tmp_path / "OpenClipper"
    openclipper.mkdir()
    instagram = tmp_path / "InstagramAgentSkill"
    instagram.mkdir()
    monkeypatch.setenv("BERRY_CHATTERBOX_ROOT", str(chatterbox))
    monkeypatch.setenv("BERRY_CHATTERBOX_PYTHON", str(python))
    monkeypatch.setenv("BERRY_HYPERFRAMES_BIN", str(hyperframes))
    monkeypatch.setenv("BERRY_OPENCLIPPER_ROOT", str(openclipper))
    monkeypatch.setenv("BERRY_INSTAGRAM_SKILL_ROOT", str(instagram))
    monkeypatch.setattr(engines, "json_request", lambda *a, **kw: (_ for _ in ()).throw(engines.EngineError("offline")))
    monkeypatch.setattr(openclipper_bridge, "status", lambda: {"online": False})
    statuses = engines.statuses()
    for name in ("chatterbox", "hyperframes", "openclipper", "instagram_agent_skill"):
        assert statuses[name]["configured"] is True
        assert statuses[name]["ready"] is False
    assert statuses["social_publishing"]["ready"] is False
