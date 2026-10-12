"""Offline integration check: run in the built image with /tmp as the working directory."""
import asyncio
import importlib.util
from pathlib import Path
import tempfile
import os

from labelbot.bot import create_bot
from labelbot.paths import RESOURCE_DIR
from labelbot.database import Database
from weasyprint import HTML


async def main():
    with tempfile.TemporaryDirectory() as directory:
        os.environ["DATABASE_PATH"] = str(Path(directory) / "database.sqlite")
        bot = create_bot()
        try:
            await bot.get_cog("LabelCog").database_ready
            assert "labelbot.cogs.labels" in bot.extensions
            await Database().execute("INSERT INTO users (display_name) VALUES (?)", ("layout-test",))
            assert (await Database().fetchone("SELECT display_name FROM users"))[0] == "layout-test"
            backends = list((RESOURCE_DIR / "templates").glob("*/backend.py"))
            assert backends
            for backend in backends:
                spec = importlib.util.spec_from_file_location("template_backend", backend)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                assert callable(module.process_data), backend
            HTML(string="<p>LabelPrint packaging check</p>").write_pdf(str(Path(directory) / "label.pdf"))
            print(f"Installed cog, SQLite, {len(backends)} template backends, and PDF rendering passed")
        finally:
            await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
