import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location("entrypoint", Path(__file__).parents[1] / "docker/entrypoint.py")
entrypoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entrypoint)


class EntrypointTests(unittest.TestCase):
    def test_dev_only_runs_bot(self):
        bot = MagicMock(returncode=2)
        bot.poll.return_value = 2
        with patch.dict(os.environ, {"ENV": "dev"}), patch.object(entrypoint.signal, "signal"), patch.object(entrypoint.subprocess, "Popen", return_value=bot) as start:
            self.assertEqual(entrypoint.main(), 2)
        self.assertEqual(start.call_count, 1)
        self.assertEqual(start.call_args.args[0], ["labelbot"])

    def test_production_stops_backup_when_bot_exits(self):
        bot = MagicMock(returncode=2)
        bot.poll.return_value = 2
        worker = MagicMock(pid=1234)
        worker.poll.return_value = None
        with patch.dict(os.environ, {"ENV": "prod"}), patch.object(entrypoint.signal, "signal"), patch.object(entrypoint.subprocess, "Popen", side_effect=[bot, worker]) as start, patch.object(entrypoint.os, "killpg") as kill:
            self.assertEqual(entrypoint.main(), 2)
        self.assertEqual(start.call_count, 2)
        kill.assert_called_once_with(1234, entrypoint.signal.SIGTERM)
        worker.wait.assert_called_once()
