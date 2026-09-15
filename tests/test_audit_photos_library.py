from __future__ import annotations

import hashlib
import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY_ROOT / "skills" / "apple-photos-curator" / "scripts" / "audit_photos_library.py"
SPEC = importlib.util.spec_from_file_location("audit_photos_library", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
AUDIT_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT_MODULE)


FULL_SCHEMA = """
create table ZASSET (
    Z_PK integer primary key,
    ZUUID text,
    ZDATECREATED real,
    ZLATITUDE real,
    ZLONGITUDE real,
    ZHIDDEN integer,
    ZTRASHEDSTATE integer,
    ZCLOUDDELETESTATE integer,
    ZUNIFORMTYPEIDENTIFIER text,
    ZISDETECTEDSCREENSHOT integer,
    ZKIND integer
)
"""


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AuditPhotosLibraryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="photos-audit-test-")
        self.root = Path(self.temporary.name)
        self.library = self.root / "Synthetic.photoslibrary"
        self.database = self.library / "database" / "Photos.sqlite"
        self.database.parent.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def create_database(self, schema: str = FULL_SCHEMA, rows: list[tuple] | None = None) -> None:
        with sqlite3.connect(self.database) as connection:
            connection.execute(schema)
            if rows is not None:
                connection.executemany(
                    """
                    insert into ZASSET values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows,
                )

    def create_full_fixture(self) -> None:
        self.create_database(
            rows=[
                (1, "asset-a", 10.0, 0.0, 0.0, 0, 0, 0, "public.jpeg", 0, 0),
                (2, "asset-b", 20.0, 0.0, 0.0, 1, 0, 0, "public.png", 1, 0),
                (3, "asset-c", 30.0, 0.0, 0.0, 0, 0, 0, "public.mpeg-4", 0, 1),
                (4, "asset-d", 40.0, 0.0, 0.0, 0, 1, 0, "public.jpeg", 0, 0),
                (5, "asset-e", 50.0, 0.0, 0.0, 0, 0, 1, "public.jpeg", 0, 0),
            ]
        )

    def test_explicit_library_requires_photos_database(self) -> None:
        missing = self.root / "Missing.photoslibrary"
        missing.mkdir()
        with self.assertRaisesRegex(SystemExit, "does not contain"):
            AUDIT_MODULE.locate_library(str(missing))

    def test_full_schema_counts_and_preserves_source_database(self) -> None:
        self.create_full_fixture()
        before_hash = file_sha256(self.database)
        before_mtime = self.database.stat().st_mtime_ns

        result = AUDIT_MODULE.audit(self.library)

        self.assertEqual(
            result["asset_counts"],
            {
                "total": 5,
                "active": 3,
                "inactive": 2,
                "hidden_active": 1,
                "screenshots_active": 1,
                "videos_active": 1,
                "nonvideo_active": 2,
            },
        )
        self.assertEqual(result["photos_quick_check"], "ok")
        self.assertRegex(result["active_metadata_fingerprint_sha256"], r"^[0-9a-f]{64}$")
        for field in (
            "photos_database_modified",
            "media_read",
            "media_deleted",
            "raw_asset_identifiers_emitted",
            "precise_gps_emitted",
        ):
            self.assertEqual(result[field], 0)
        self.assertEqual(file_sha256(self.database), before_hash)
        self.assertEqual(self.database.stat().st_mtime_ns, before_mtime)

    def test_fingerprint_is_deterministic_and_tracks_active_metadata(self) -> None:
        self.create_full_fixture()
        first = AUDIT_MODULE.audit(self.library)["active_metadata_fingerprint_sha256"]
        second = AUDIT_MODULE.audit(self.library)["active_metadata_fingerprint_sha256"]
        self.assertEqual(first, second)

        with sqlite3.connect(self.database) as connection:
            connection.execute("update ZASSET set ZDATECREATED = 31 where Z_PK = 3")
        changed = AUDIT_MODULE.audit(self.library)["active_metadata_fingerprint_sha256"]
        self.assertNotEqual(first, changed)

    def test_reduced_schema_uses_safe_fallbacks(self) -> None:
        self.create_database("create table ZASSET (Z_PK integer primary key)")
        with sqlite3.connect(self.database) as connection:
            connection.executemany("insert into ZASSET (Z_PK) values (?)", [(1,), (2,)])

        result = AUDIT_MODULE.audit(self.library)

        self.assertEqual(result["asset_counts"]["total"], 2)
        self.assertEqual(result["asset_counts"]["active"], 2)
        self.assertEqual(result["asset_counts"]["inactive"], 0)
        self.assertEqual(result["asset_counts"]["hidden_active"], 0)
        self.assertEqual(result["asset_counts"]["screenshots_active"], 0)
        self.assertEqual(result["asset_counts"]["videos_active"], 0)
        self.assertEqual(result["asset_counts"]["nonvideo_active"], 2)

    def test_unsupported_schema_is_rejected(self) -> None:
        self.create_database("create table ZASSET (ZNAME text)")
        with self.assertRaisesRegex(SystemExit, "ZASSET.Z_PK is missing"):
            AUDIT_MODULE.audit(self.library)

    def test_cli_stdout_matches_written_json(self) -> None:
        self.create_full_fixture()
        output = self.root / "audit.json"

        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--library", str(self.library), "--output", str(output)],
            check=True,
            capture_output=True,
            text=True,
        )

        stdout_payload = json.loads(completed.stdout)
        file_payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(stdout_payload, file_payload)
        self.assertNotIn("asset-a", completed.stdout)
        self.assertNotIn("ZLATITUDE", completed.stdout)
        self.assertEqual(stdout_payload["raw_asset_identifiers_emitted"], 0)
        self.assertEqual(stdout_payload["precise_gps_emitted"], 0)


if __name__ == "__main__":
    unittest.main()
