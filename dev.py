"""Start the local development server with safe reload directories."""

import os
import sys
from pathlib import Path

import uvicorn


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
WEB_DIR = PROJECT_ROOT / "web"

# Do not depend on an editable-install .pth file, which macOS can mark hidden.
sys.path.insert(0, str(SRC_DIR))


if __name__ == "__main__":
    uvicorn.run(
        "cafe_crew.api:app",
        host="127.0.0.1",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
        reload_dirs=[str(SRC_DIR), str(WEB_DIR)],
    )

