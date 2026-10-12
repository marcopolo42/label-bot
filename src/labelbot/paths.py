"""Read-only package resources and separately configured runtime storage."""
import os
from pathlib import Path

RESOURCE_DIR = Path(__file__).resolve().parent / "resources"


def get_resource_path(*parts):
    return str(RESOURCE_DIR.joinpath(*parts))


def get_database_path():
    if os.environ.get("DATABASE_PATH"):
        return Path(os.environ["DATABASE_PATH"]).expanduser().resolve()
    return Path(os.environ.get("DATA_DIR", "data")).expanduser().resolve() / "database.sqlite"
