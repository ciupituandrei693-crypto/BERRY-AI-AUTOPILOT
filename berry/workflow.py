"""Local editorial QA, schedule, publication packages and backups.

No social APIs, cloud calls, remote downloads or payments are implemented here.
Only explicit, approved, human-reviewed files can be exported.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import db, studio

PLATFORMS = ("youtube", "tiktok", "instagram")
FLAGS = ("facts_checked", "visual_rights", "voice_rights", "music_rights", "disclosure_checked")
MAX_PACKAGES = 500


def init() -> None:
    with db.connection() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS review_meta(
          item_id INTEGER PRIMARY KEY REFERENCES items(id) ON DELETE CASCADE,
          facts_checked INTEGER NOT NULL DEFAULT 0,
          visual_rights INTEGER NOT NULL DEFAULT 0,
          voice_rights INTEGER NOT NULL DEFAULT 0,
          music_rights INTEGER NOT NULL DEFAULT 0,
          disclosure_checked INTEGER NOT NULL DEFAULT 0,
          notes TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS publication_schedule(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          item_id INTEGER NOT NULL REFERENCES items(id),
          platform TEXT NOT NULL,
          scheduled_at TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'SCHEDULED_LOCAL',
          qa_fingerprint TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          UNIQUE(item_id, platform, scheduled_at));
        CREATE TABLE IF NOT EXISTS qa_history(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          item_id INTEGER NOT NULL REFERENCES items(id),
          passed INTEGER NOT NULL,
          fingerprint TEXT NOT NULL,
          details_json TEXT NOT NULL,
          created_at TEXT NOT NULL);
        ''')


def meta(item_id: int) -> dict:
    row = db.one_row("SELECT * FROM review_meta WHERE item_id=?", (item_id,))
    return row or {"item_id": item_id, **{k: 0 for k in FLAGS}, "notes": "", "updated_at": None}


def save_meta(item_id: int, flags: dict, notes: str = "") -> dict:
    item = db.one_row("SELECT * FROM items WHERE id=?", (item_id,))
    if not item:
        raise LookupError("Materialul nu există")
    if item["status"] != "DRAFT":
        raise ValueError("Drepturile și verificările se modifică doar în DRAFT; aprobările existente nu pot fi schimbate")
    values = [int(bool(flags.get(k, False))) for k in FLAGS]
    with db.connection() as con:
        con.execute("""INSERT INTO review_meta(item_id,facts_checked,visual_rights,voice_rights,music_rights,disclosure_checked,notes,updated_at)
          VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(item_id) DO UPDATE SET
          facts_checked=excluded.facts_checked,visual_rights=excluded.visual_rights,
          voice_rights=excluded.voice_rights,music_rights=excluded.music_rights,
          disclosure_checked=excluded.disclosure_checked,notes=excluded.notes,updated_at=excluded.updated_at""",
          (item_id, *values, notes[:1000], db.utcnow()))
        db.audit(con, "rights_review_changed", {"item_id": item_id, "flags": dict(zip(FLAGS, values))})
    return meta(item_id)


def _fingerprint(item: dict, job: dict | None, flags: dict) -> str:
    data = {
        "item": {k: item.get(k) for k in ("id", "title", "topic", "content_type", "seo_json")},
        "job": {k: job.get(k) for k in ("id", "mode", "status", "result_json", "updated_at")} if job else None,
        "flags": {k: int(bool(flags[k])) for k in FLAGS},
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def quality(item_id: int, *, save: bool = False) -> dict:
    item = db.one_row("SELECT * FROM items WHERE id=?", (item_id,))
    if not item:
        raise LookupError("Materialul nu există")
    flags = meta(item_id)
    job = db.one_row("SELECT * FROM render_jobs WHERE item_id=? ORDER BY id DESC LIMIT 1", (item_id,))
    reasons, warnings = [], []
    if len(item["topic"].strip()) < 8:
        reasons.append("Subiectul trebuie să fie descriptiv (minimum 8 caractere)")
    if len(item["title"].strip()) < 10:
        reasons.append("Titlul trebuie să aibă minimum 10 caractere")
    try:
        seo = json.loads(item.get("seo_json") or "{}")
    except json.JSONDecodeError:
        seo = {}
    if not seo.get("hook") or not seo.get("hashtags"):
        reasons.append("Pachetul SEO este incomplet")
    if not job or job["status"] != "DONE" or job["mode"] != "full":
        reasons.append("Lipsește randarea completă locală (mod FULL, stare DONE)")
    else:
        result = json.loads(job["result_json"] or "{}")
        if item["content_type"] != "image" and not result.get("video_created"):
            reasons.append("Nu există MP4 complet")
        if item["content_type"] == "image" and not result.get("image_created"):
            reasons.append("Nu există imagine exportabilă")
        if item["content_type"] != "image" and result.get("render_kind") == "IMPORTED_OR_GENERATED_LOCAL_VIDEO":
            actual = result.get("rendered_duration_seconds")
            target = result.get("target_duration_seconds")
            if actual is None or target is None or abs(actual - target) > 2:
                reasons.append("Durata MP4 local nu corespunde formatului; verifică 15/90/300 secunde")
        if result.get("render_kind") != "AI_3D_ANIMATION":
            warnings.append("Material concept/motion graphics; nu este animație 3D AI")
        if item["channel_id"] == "beats" and not (result.get("music_generated") or result.get("music_supplied")):
            warnings.append("Nu există încă o melodie originală generată; verifică manual cerința canalului")
    for flag, label in {
        "facts_checked": "Verifică informațiile și afirmațiile",
        "visual_rights": "Confirmă drepturile asupra imaginilor și personajelor",
        "voice_rights": "Confirmă drepturile și consimțământul pentru voce",
        "music_rights": "Confirmă drepturile pentru muzică (inclusiv absența ei)",
        "disclosure_checked": "Verifică regulile platformei și divulgarea conținutului AI",
    }.items():
        if not flags[flag]:
            reasons.append(label)
    if item["channel_id"] == "beats" and not (job and job["status"] == "DONE" and
            (json.loads(job["result_json"] or "{}").get("music_generated") or
             json.loads(job["result_json"] or "{}").get("music_supplied"))):
        reasons.append("FRUIT BEATS: încarcă o piesă originală înainte de export")
    fp = _fingerprint(item, job, flags)
    out = {"item_id": item_id, "passed": not reasons, "reasons": reasons, "warnings": warnings,
           "fingerprint": fp, "job_id": job["id"] if job else None,
           "render_kind": json.loads(job["result_json"] or "{}").get("render_kind") if job else None,
           "manual_checks": {k: bool(flags[k]) for k in FLAGS}, "publication_enabled": False}
    if save:
        with db.connection() as con:
            con.execute("INSERT INTO qa_history(item_id,passed,fingerprint,details_json,created_at) VALUES(?,?,?,?,?)",
                        (item_id, int(out["passed"]), fp, json.dumps(out, ensure_ascii=False), db.utcnow()))
            db.audit(con, "local_qa_checked", {"item_id": item_id, "passed": out["passed"]})
    return out


def schedule(item_id: int, platform: str, scheduled_at: str) -> dict:
    if platform not in PLATFORMS:
        raise ValueError("Platformă invalidă")
    try:
        when = datetime.fromisoformat(scheduled_at)
    except ValueError as exc:
        raise ValueError("Data trebuie să fie ISO 8601, cu fus orar") from exc
    if when.tzinfo is None or when.utcoffset() is None:
        raise ValueError("Ora trebuie să includă fusul orar, de ex. +02:00")
    if when.astimezone(timezone.utc) <= datetime.now(timezone.utc):
        raise ValueError("Alege o dată viitoare")
    item = db.one_row("SELECT * FROM items WHERE id=?", (item_id,))
    if not item:
        raise LookupError("Materialul nu există")
    if item["status"] != "APPROVED_NOT_PUBLISHED":
        raise ValueError("Materialul trebuie aprobat de un om înainte de programare")
    report = quality(item_id)
    if not report["passed"]:
        raise ValueError("QA incomplet: " + "; ".join(report["reasons"][:4]))
    now = db.utcnow()
    with db.connection() as con:
        try:
            cur = con.execute("INSERT INTO publication_schedule(item_id,platform,scheduled_at,qa_fingerprint,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                              (item_id, platform, when.isoformat(), report["fingerprint"], now, now))
        except sqlite3.IntegrityError as exc:
            raise ValueError("Programarea există deja") from exc
        db.audit(con, "scheduled_local_only", {"schedule_id": cur.lastrowid, "item_id": item_id, "platform": platform})
        return {"id": cur.lastrowid, "status": "SCHEDULED_LOCAL", "published": False}


def calendar() -> list[dict]:
    rows = db.all_rows("""SELECT s.*, i.title, i.channel_id, i.content_type
                         FROM publication_schedule s JOIN items i ON i.id=s.item_id
                         ORDER BY s.scheduled_at ASC LIMIT 500""")
    for row in rows:
        if row["status"] == "SCHEDULED_LOCAL":
            try:
                row["qa_still_valid"] = quality(row["item_id"])["fingerprint"] == row["qa_fingerprint"]
            except LookupError:
                row["qa_still_valid"] = False
    return rows


def cancel_schedule(schedule_id: int) -> dict:
    with db.connection() as con:
        row = con.execute("SELECT status FROM publication_schedule WHERE id=?", (schedule_id,)).fetchone()
        if not row:
            raise LookupError("Programarea nu există")
        if row["status"] != "SCHEDULED_LOCAL":
            raise ValueError("Programarea nu mai poate fi anulată")
        con.execute("UPDATE publication_schedule SET status='CANCELLED',updated_at=? WHERE id=?", (db.utcnow(), schedule_id))
        db.audit(con, "schedule_cancelled", {"schedule_id": schedule_id})
    return {"status": "CANCELLED", "published": False}


def package(schedule_id: int) -> tuple[bytes, str]:
    row = db.one_row("""SELECT s.*,i.title,i.channel_id,i.content_type,i.seo_json
                        FROM publication_schedule s JOIN items i ON i.id=s.item_id WHERE s.id=?""", (schedule_id,))
    if not row:
        raise LookupError("Programarea nu există")
    if row["status"] not in ("SCHEDULED_LOCAL", "EXPORTED_LOCAL"):
        raise ValueError("Programarea nu este activă")
    qa = quality(row["item_id"])
    if not qa["passed"] or qa["fingerprint"] != row["qa_fingerprint"]:
        raise ValueError("QA a fost modificat sau a expirat; revizuiește materialul")
    job = studio.get_job(qa["job_id"])
    if not job:
        raise ValueError("Randarea lipsește")
    selected = {"script", "subtitles", "manifest", "image", "voice", "video", "soundtrack"}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        seo = json.loads(row["seo_json"] or "{}")
        z.writestr("SEO_AND_CAPTIONS.json", json.dumps({"title": row["title"], "platform": row["platform"],
            "scheduled_at": row["scheduled_at"], "seo": seo, "published": False}, ensure_ascii=False, indent=2))
        z.writestr("QA_REPORT.json", json.dumps(qa, ensure_ascii=False, indent=2))
        z.writestr("README.txt", "BERRY LOCAL EXPORT. Acest pachet NU a fost publicat.\n"
                   "Verifică manual fiecare fișier și regulile platformei înainte de postare.\n")
        for kind in selected:
            path = studio.output_file(job["id"], kind)
            if path and path.is_file():
                z.write(path, path.name)
    if buffer.tell() > 150_000_000:
        raise ValueError("Pachetul depășește limita de 150 MB")
    with db.connection() as con:
        con.execute("UPDATE publication_schedule SET status='EXPORTED_LOCAL',updated_at=? WHERE id=?", (db.utcnow(), schedule_id))
        db.audit(con, "publication_package_exported_no_post", {"schedule_id": schedule_id})
    return buffer.getvalue(), f"BERRY_{row['platform']}_{schedule_id}.zip"


def backup() -> tuple[bytes, str]:
    """Consistent SQLite snapshot, not a dump of running DB file; no external storage."""
    buffer = io.BytesIO()
    snapshot = io.BytesIO()
    with sqlite3.connect(":memory:") as dest:
        with db.connection() as source:
            source.backup(dest)
        # sqlite3 serialize available in Python 3.11+
        data = dest.serialize()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("berry.sqlite3", data)
        z.writestr("README.txt", "Copie locală SQLite BERRY. Include subiecte, audit și propuneri; păstreaz-o privat.\n")
    with db.connection() as con:
        db.audit(con, "local_backup_downloaded", {"bytes": len(data)})
    return buffer.getvalue(), "BERRY_BACKUP_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".zip"
