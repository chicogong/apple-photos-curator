#!/usr/bin/env python3
"""Print a privacy-safe, read-only aggregate audit of an Apple Photos library."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path


def locate_library(value: str | None) -> Path:
    if value:
        library = Path(value).expanduser().resolve()
    else:
        candidates = sorted((Path.home() / "Pictures").glob("*.photoslibrary"))
        if len(candidates) != 1:
            raise SystemExit("Pass --library when zero or multiple Photos libraries are present.")
        library = candidates[0].resolve()
    database = library / "database" / "Photos.sqlite"
    if not database.is_file():
        raise SystemExit("The selected package does not contain database/Photos.sqlite.")
    return library


def copied_connection(database: Path):
    temporary = tempfile.TemporaryDirectory(prefix="photos-safe-audit-")
    target = Path(temporary.name) / "Photos.sqlite"
    shutil.copy2(database, target)
    for suffix in ("-wal", "-shm"):
        source = Path(str(database) + suffix)
        if source.exists():
            shutil.copy2(source, Path(str(target) + suffix))
    connection = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("pragma query_only=on")
    return temporary, connection


def columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"pragma table_info({table})")}


def expr(available: set[str], name: str, fallback: str = "0") -> str:
    return f"coalesce({name},0)" if name in available else fallback


def active_where(available: set[str]) -> str:
    checks = []
    for name in ("ZTRASHEDSTATE", "ZCLOUDDELETESTATE"):
        if name in available:
            checks.append(f"coalesce({name},0)=0")
    return " and ".join(checks) or "1=1"


def scalar(connection: sqlite3.Connection, sql: str) -> int:
    return int(connection.execute(sql).fetchone()[0])


def metadata_fingerprint(connection: sqlite3.Connection, available: set[str], where: str) -> str:
    fields = [name for name in (
        "Z_PK", "ZUUID", "ZDATECREATED", "ZLATITUDE", "ZLONGITUDE",
        "ZHIDDEN", "ZTRASHEDSTATE", "ZCLOUDDELETESTATE", "ZUNIFORMTYPEIDENTIFIER",
    ) if name in available]
    digest = hashlib.sha256()
    query = f"select {','.join(fields)} from ZASSET where {where} order by Z_PK"
    for row in connection.execute(query):
        digest.update(json.dumps(list(row), ensure_ascii=False, separators=(",", ":")).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def audit(library: Path) -> dict:
    temporary, connection = copied_connection(library / "database" / "Photos.sqlite")
    try:
        available = columns(connection, "ZASSET")
        if "Z_PK" not in available:
            raise SystemExit("Unsupported Photos schema: ZASSET.Z_PK is missing.")
        where = active_where(available)
        total = scalar(connection, "select count(*) from ZASSET")
        active = scalar(connection, f"select count(*) from ZASSET where {where}")
        hidden = scalar(connection, f"select count(*) from ZASSET where {where} and {expr(available, 'ZHIDDEN')}<>0")
        screenshot = scalar(connection, f"select count(*) from ZASSET where {where} and {expr(available, 'ZISDETECTEDSCREENSHOT')}<>0")
        video = scalar(connection, f"select count(*) from ZASSET where {where} and {expr(available, 'ZKIND')}=1")
        return {
            "mode": "read_only_copied_database_aggregate",
            "library_name": library.name,
            "photos_quick_check": str(connection.execute("pragma quick_check").fetchone()[0]),
            "asset_counts": {
                "total": total,
                "active": active,
                "inactive": total - active,
                "hidden_active": hidden,
                "screenshots_active": screenshot,
                "videos_active": video,
                "nonvideo_active": active - video,
            },
            "active_metadata_fingerprint_sha256": metadata_fingerprint(connection, available, where),
            "photos_database_modified": 0,
            "media_read": 0,
            "media_deleted": 0,
            "raw_asset_identifiers_emitted": 0,
            "precise_gps_emitted": 0,
        }
    finally:
        connection.close()
        temporary.cleanup()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", help="path to a .photoslibrary package")
    parser.add_argument("--output", help="optional JSON output path")
    args = parser.parse_args()
    payload = audit(locate_library(args.library))
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).expanduser().write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
