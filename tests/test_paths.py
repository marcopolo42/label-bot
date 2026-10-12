import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from labelbot.paths import get_database_path, get_resource_path
from labelbot.config import Config


class PathTests(unittest.TestCase):
    def test_packaged_resources_load_outside_checkout(self):
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                self.assertTrue(Path(get_resource_path("templates", "fridge", "template.html")).is_file())
                config = Config()
                config.load_config_files()
                self.assertTrue(config.get("templates"))
            finally:
                os.chdir(original)

    def test_default_and_explicit_database_paths(self):
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            try:
                os.chdir(directory)
                self.assertEqual(get_database_path(), Path(directory).resolve() / "data/database.sqlite")
                os.environ["DATABASE_PATH"] = "custom/db.sqlite"
                self.assertEqual(get_database_path(), Path("custom/db.sqlite").resolve())
            finally:
                os.chdir(original)
