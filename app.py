"""Vercel entrypoint for the FastAPI application."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

# Vercel installs the dependencies declared in pyproject.toml, while the
# application itself uses a src/ layout. Add it explicitly so the entrypoint
# behaves the same way in Vercel and in a fresh local checkout.
sys.path.insert(0, str(SRC_DIR))

from cafe_crew.api import app  # noqa: E402,F401
