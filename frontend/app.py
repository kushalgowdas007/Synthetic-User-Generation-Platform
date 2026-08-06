from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

spec = importlib.util.spec_from_file_location("root_streamlit_app", ROOT_DIR / "app.py")
root_app = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(root_app)


if __name__ == "__main__":
    root_app.main()
