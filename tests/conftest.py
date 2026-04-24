from __future__ import annotations

import sys
import types
from pathlib import Path
from uuid import uuid4

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

folder_paths = types.ModuleType("folder_paths")
folder_paths.get_output_directory = lambda: str(REPO_ROOT / "test-output")
sys.modules.setdefault("folder_paths", folder_paths)


@pytest.fixture
def workspace_tmp_path():
    base_dir = REPO_ROOT / "output" / "test-tmp"
    base_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = base_dir / uuid4().hex
    tmp_dir.mkdir()
    yield tmp_dir
