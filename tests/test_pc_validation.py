"""PC validation tests without requiring Blender, FFmpeg or Windows in CI."""
from pathlib import Path

from tools import pc_validation


def test_validation_step_shape():
    step = pc_validation._step("test", "PASS", "ok", 1.2345)
    assert step == {"name": "test", "status": "PASS", "detail": "ok",
                    "elapsed_seconds": 1.23}


def test_api_smoke_uses_temporary_database(tmp_path):
    from berry import db
    old = db.DB
    step = pc_validation._api_smoke(tmp_path)
    assert step["status"] == "PASS", step
    assert db.DB == old
    assert (tmp_path / "smoke.sqlite3").is_file()


def test_validation_never_marks_external_phase_ready(monkeypatch):
    from berry import diagnostics, model_bridge
    monkeypatch.setattr(diagnostics, "report", lambda: {"local_only": True})
    monkeypatch.setattr(model_bridge, "status", lambda name: {"ready": False})
    monkeypatch.setattr(pc_validation, "_api_smoke",
                        lambda tmp: pc_validation._step("API", "PASS"))
    monkeypatch.setattr(pc_validation, "_ffmpeg_benchmark",
                        lambda tmp: pc_validation._step("FFmpeg", "SKIP"))
    monkeypatch.setattr(pc_validation, "_exe_smoke",
                        lambda: pc_validation._step("EXE", "SKIP"))
    report = pc_validation.validate(full=False, tests=False)
    assert report["local_only"] is True
    assert report["external_server_connected"] is False
    assert report["cloud_gpu_used"] is False
    assert report["social_publishing_enabled"] is False
    assert report["ready_for_external_phase"] is False
    assert report["counts"]["SKIP"] >= 2
