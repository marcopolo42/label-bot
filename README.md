LabelPrint
===========

This repository contains tools for label generation and a Discord bot.

Install locally with pipx
------------------------

To install the package locally with pipx (from any path):

```bash
# Install from the project directory
pipx install /Users/mbelarbi/Developer/LabelPrint42/LabelPrintDev

# Reinstall / upgrade the local install
pipx upgrade --include-deps labelprint || pipx install --force /Users/mbelarbi/Developer/LabelPrint42/LabelPrintDev
```

For development you may prefer an editable install in a virtualenv instead of pipx:

```bash
# From project root -- installs into the current Python environment (not recommended globally)
python3 -m pip install -e .
```

Available CLI entry points after install:
- `labelbot` — launches the Discord bot (reads DISCORD_TOKEN from environment)

Notes
-----
- Ensure your environment satisfies the Python version (>=3.8) and system dependencies.
- The project ships with `label_cog` package which includes templates and assets required by the CLI tools.

License
-------
This project is licensed under the GNU Affero General Public License v3 (AGPL-3.0-or-later).
You can find the license terms at https://www.gnu.org/licenses/agpl-3.0.en.html. If you plan to redistribute
or modify this software, make sure you comply with the AGPL requirements.


