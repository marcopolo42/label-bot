import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from labelbot import bot


class StartupTests(unittest.TestCase):
    def test_cli_reads_env_from_launch_directory(self):
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            try:
                os.chdir(directory)
                Path('.env').write_text('DISCORD_TOKEN=test-token\n')
                with patch.object(bot, 'create_bot') as factory:
                    bot.main()
                    factory.return_value.run.assert_called_once_with('test-token')
            finally:
                os.chdir(original)
