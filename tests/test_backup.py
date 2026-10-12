from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from labelbot.backup import backup


class BackupTests(unittest.TestCase):
    def test_snapshot_includes_committed_wal_and_excludes_uncommitted_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "live.sqlite"
            target = Path(directory) / "snapshot.sqlite"
            with sqlite3.connect(source) as writer:
                writer.execute("PRAGMA journal_mode=WAL")
                writer.execute("CREATE TABLE items (value TEXT)")
                writer.execute("INSERT INTO items VALUES ('committed')")
                writer.commit()
                writer.execute("INSERT INTO items VALUES ('pending')")
                backup.snapshot(source, target)
                with sqlite3.connect(target) as restored:
                    self.assertEqual(restored.execute("SELECT * FROM items").fetchall(), [("committed",)])
                    self.assertEqual(restored.execute("PRAGMA integrity_check").fetchone(), ("ok",))

    def test_missing_source_does_not_create_database_or_replace_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "missing.sqlite"
            target = Path(directory) / "snapshot.sqlite"
            target.write_bytes(b"previous snapshot")
            with self.assertRaises(sqlite3.OperationalError):
                backup.snapshot(source, target)
            self.assertFalse(source.exists())
            self.assertEqual(target.read_bytes(), b"previous snapshot")

    def test_failed_snapshot_never_uploads(self):
        with patch.object(backup, "snapshot", side_effect=RuntimeError), patch.object(backup, "restic") as restic:
            with self.assertRaises(RuntimeError):
                backup.backup()
            restic.assert_not_called()

    def test_failed_upload_never_prunes(self):
        with patch.object(backup, "snapshot"), patch.object(backup, "restic", side_effect=RuntimeError) as restic:
            with self.assertRaises(RuntimeError):
                backup.backup()
            self.assertEqual(restic.call_count, 1)
            self.assertEqual(restic.call_args.args[0], "backup")


class PasswordTransportTests(unittest.TestCase):
    def test_password_is_passed_in_environment_not_command(self):
        import os
        import shlex
        with patch.dict(os.environ, {
            "RESTIC_REPOSITORY": "sftp://marcopolo@sol.usbx.me:22/labelbot-backups",
            "SFTP_PASSWORD": "test-secret",
        }), patch.object(backup.subprocess, "run") as run:
            backup.restic("snapshots")
        args = run.call_args.args[0]
        self.assertNotIn("test-secret", " ".join(args))
        self.assertEqual(run.call_args.kwargs["env"]["SSHPASS"], "test-secret")
        self.assertEqual(shlex.split(args[2].split("=", 1)[1]),
                         ["sshpass", "-e", "ssh", "-p", "22", "-l", "marcopolo",
                          "-s", "--", "sol.usbx.me", "sftp"])


if __name__ == "__main__":
    unittest.main()
