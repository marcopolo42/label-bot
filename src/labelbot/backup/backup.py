"""Consistent SQLite snapshots followed by encrypted restic backups."""
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import shlex
from urllib.parse import urlsplit, unquote
import subprocess
import sys
import time


def snapshot(source, destination):
    source, destination = Path(source).resolve(), Path(destination)
    if source == destination.resolve():
        raise ValueError("Snapshot destination must differ from the live database")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    deadline = time.monotonic() + 120

    def progress(status, remaining, total):
        if time.monotonic() > deadline:
            raise TimeoutError("SQLite snapshot exceeded 120 seconds")

    try:
        # mode=ro refuses to silently create an empty DB when the source is missing.
        with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as src:
            with closing(sqlite3.connect(temporary)) as dst:
                src.backup(dst, pages=256, progress=progress)
                if dst.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                    raise RuntimeError("SQLite snapshot failed integrity_check")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def restic(*args):
    command = ["restic"]
    environment = os.environ.copy()
    if environment.get("SFTP_PASSWORD"):
        environment["SSHPASS"] = environment["SFTP_PASSWORD"]
        repository = urlsplit(environment["RESTIC_REPOSITORY"])
        if repository.scheme != "sftp" or not repository.hostname or not repository.username:
            raise ValueError("Use RESTIC_REPOSITORY=sftp://user@host:22/path")
        ssh = ["sshpass", "-e", "ssh", "-p", str(repository.port or 22),
               "-l", unquote(repository.username), "-s", "--", repository.hostname, "sftp"]
        command += ["-o", "sftp.command=" + shlex.join(ssh)]
    subprocess.run([*command, *args], env=environment, check=True, timeout=3600)


def backup():
    snapshot(os.environ.get("DATABASE_PATH", "/data/database.sqlite"),
             "/snapshot/database.sqlite")
    host = os.environ.get("RESTIC_HOST", "labelbot-production")
    restic("backup", "/snapshot/database.sqlite", "--host", host, "--tag", "labelbot-sqlite")
    # Only apply retention after a successful upload, scoped to this backup set.
    restic("forget", "--host", host, "--tag", "labelbot-sqlite", "--path",
           "/snapshot/database.sqlite", "--keep-daily", "7", "--keep-weekly", "4",
           "--keep-monthly", "12", "--prune")
    Path("/tmp/last-success").write_text(str(time.time()))
    print("SQLite backup and retention completed", flush=True)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "health":
        if os.environ.get("ENV") != "prod":
            return 0
        age = time.time() - float(Path("/tmp/last-success").read_text())
        return 0 if age < int(os.environ.get("BACKUP_INTERVAL_SECONDS", "86400")) + 7200 else 1
    if os.environ.get("ENV") != "prod":
        raise RuntimeError("Backups require ENV=prod")
    if not os.environ.get("RESTIC_REPOSITORY", "").startswith("sftp:"):
        raise RuntimeError("Set RESTIC_REPOSITORY to an SFTP repository")
    if len(sys.argv) > 1 and sys.argv[1] != "--once":
        restic(*sys.argv[1:])
        return 0
    interval = int(os.environ.get("BACKUP_INTERVAL_SECONDS", "86400"))
    if interval < 60:
        raise ValueError("BACKUP_INTERVAL_SECONDS must be at least 60")
    while True:
        try:
            backup()
        except Exception as error:
            if "--once" in sys.argv:
                raise
            print(f"Backup failed: {error}. Retrying in 5 minutes.", flush=True)
            time.sleep(300)
            continue
        if "--once" in sys.argv:
            return 0
        time.sleep(interval)


if __name__ == "__main__":
    sys.exit(main())
