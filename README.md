# LabelPrint

A Discord bot for generating labels and printing them on Brother QL printers.
Requires Python 3.11 or newer. Discord integration uses Pycord.

## Project layout

```text
src/labelbot/
  bot.py            Bot factory and CLI startup
  __main__.py       python -m labelbot
  backup/           SQLite snapshots, restic worker, and SSH configuration
  cogs/             Discord commands and listeners
  ui/               Discord views, modals, and response helpers
  services/         Printing, coins, uploads, and admin operations
  rendering/        Labels, templates, and image rendering
  resources/        Packaged templates, YAML configuration, images, and emojis
  config.py         Configuration loader
  database.py       SQLite access
  paths.py          Resource and runtime paths
  session.py        User session models
  state.py          Pending upload state
  logging.py        Logging setup
  utils.py          Shared helpers

docker/             Container process startup
tests/              Automated checks
docs/reference/     Template examples, role and emoji notes
data/               Local runtime data (ignored by Git)
```

Templates retain their HTML, CSS, optional Python backend, and associated images
in one folder under `src/labelbot/resources/templates/`. Resources are resolved
relative to the installed package, so the bot can run outside the repository.

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp example.env .env  # only if you do not already have .env
# Fill in Discord/printer settings, then:
labelbot
# Equivalent:
python -m labelbot
```

Use `pipx install .` for an isolated CLI installation. Native Pango dependencies
are required for rendering; the Docker image installs them automatically.
`pyproject.toml` defines the package and its dependencies.

New local databases default to `data/database.sqlite`. Set `DATABASE_PATH` for
an explicit location. The local database has been moved to `data/database.sqlite`.
For older checkouts, stop the bot and migrate `label_cog/database.sqlite` before
starting the new version.
Docker continues using `/data/database.sqlite` in its persistent volume.

Run tests after installing the package:

```bash
python -m unittest discover -s tests -v
```

Docker (USB or network printer)
-------------------------------

Use the single `docker-compose.yml` for either printer type. Set the printer
settings in `.env` using `example.env` as a guide. USB passthrough requires a Linux
Docker host; network printing also works with Docker Desktop.

SQLite lives in the named `labelbot-data` volume at `/data/database.sqlite`.
Rebuilds and `docker compose down` preserve it. **Do not use `down -v`**, which
removes the volume. Code, templates, and configuration are built into the image;
rebuild after changing them. No database or credentials are copied into the image.
The old development startup behavior that deleted the database has been removed.

### Existing database: migrate once before starting the new version

The old Compose file stored SQLite in `label_cog/database.sqlite` in the host
checkout. This checkout now uses `data/database.sqlite`. Stop the old bot, then
copy a consistent snapshot into the new volume. If upgrading an older checkout,
use `$PWD/label_cog` instead of `$PWD/data` in the mount below.
The command refuses to overwrite an existing destination. Keep the old file.
Skip this step for a new installation.

```bash
docker compose stop labelbot
docker compose build
docker compose run --rm --no-deps --entrypoint python \
  -v "$PWD/data:/legacy" labelbot -c '
from pathlib import Path
import sqlite3
source = Path("/legacy/database.sqlite")
target = Path("/data/database.sqlite")
assert source.is_file(), "Locate the old database before continuing"
assert not target.exists(), "Destination already exists"
with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as src:
    with sqlite3.connect(target) as dst:
        src.backup(dst)
        assert dst.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
'
```

If the old deployment did not mount the checkout, recover its database and any
WAL/SHM files from the stopped container first; do not delete that container.

### Production backups

Set `ENV=prod`, `RESTIC_REPOSITORY`, `SFTP_PASSWORD`, and `RESTIC_PASSWORD` in `.env`.
The restic password encrypts the backups and is separate from the SFTP password.
Keep a recovery copy of it. `.env` is ignored by Git and excluded from the image.
The repository is `/home/marcopolo/backups/labelbot` on `sol.usbx.me:22`.
The double slash after the port in `RESTIC_REPOSITORY` makes the path absolute.

Initialize a new repository once, then start the bot:

```bash
docker compose build
docker compose run --rm --no-deps --entrypoint python labelbot -m labelbot.backup init
docker compose up -d
```

For an existing repository, skip `init` and use its original encryption password.
SSH remembers the first host key in `/data/known_hosts` and rejects later changes
(trust on first use). A verified known-hosts file can be placed there beforehand.

The bot and backup worker run inside the same container. Backups run immediately
and every 24 hours afterwards, using a consistent SQLite snapshot. Failed backups
retry after five minutes without stopping the bot. Successful backups retain
7 daily, 4 weekly, and 12 monthly snapshots. `ENV=dev` runs only the bot.

```bash
docker compose logs --tail=100 labelbot
docker compose ps
# List backups using the configured SFTP password:
docker compose exec labelbot python -m labelbot.backup snapshots
```

A stale backup makes the container unhealthy; connect Docker health monitoring to
your alerting system if you need notifications. Docker does not send alerts itself.

### Restore

Stop the bot first. Replace `SNAPSHOT_ID` below with an ID from `snapshots`:

```bash
docker compose stop labelbot
mkdir -p restore
docker compose run --rm --no-deps -v "$PWD/restore:/restore" \
  --entrypoint python labelbot -m labelbot.backup restore SNAPSHOT_ID --target /restore
```

The restored database is `restore/snapshot/database.sqlite`. Validate it and replace
the live database while the bot remains stopped. This preserves the old database
and sidecars in a rollback directory:

```bash
docker compose run --rm --no-deps -v "$PWD/restore:/restore:ro" \
  --entrypoint python labelbot -c '
from pathlib import Path
import sqlite3, shutil, time
source = Path("/restore/snapshot/database.sqlite")
with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as db:
    assert db.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
rollback = Path("/data/rollback-" + str(time.time_ns()))
rollback.mkdir()
for name in ("database.sqlite", "database.sqlite-wal", "database.sqlite-shm", "database.sqlite-journal"):
    path = Path("/data") / name
    if path.exists():
        path.rename(rollback / name)
shutil.copyfile(source, "/data/database.sqlite")
'
docker compose up -d
```

Backups cover the database; keep application configuration and credentials separately.

## License

GNU Affero General Public License v3 (AGPL-3.0-or-later).
