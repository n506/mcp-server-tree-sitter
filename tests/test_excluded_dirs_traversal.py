from pathlib import Path
from types import SimpleNamespace

import pytest

from mcp_server_tree_sitter.tools.analysis import analyze_project_structure
from mcp_server_tree_sitter.tools.file_operations import list_project_files
from mcp_server_tree_sitter.tools.search import search_text


class DummyProject:
    """
    Minimal project stub compatible with tool functions.
    """

    def __init__(self, root_path: Path):
        self.root_path = root_path


@pytest.fixture
def sample_project(tmp_path: Path) -> DummyProject:
    """
    Create a test project with excluded directories.

    Layout:

    tmp/
      src/app.py
      src/other.py
      .venv/lib/site-packages/pkg.py
      node_modules/lib.js
    """

    (tmp_path / "src").mkdir()
    (tmp_path / ".venv" / "lib" / "site-packages").mkdir(parents=True)
    (tmp_path / "node_modules").mkdir()

    (tmp_path / "src" / "app.py").write_text(
        "def public_function():\n"
        "    return 'app'\n",
        encoding="utf-8",
    )

    (tmp_path / "src" / "other.py").write_text(
        "def other_function():\n"
        "    return 'other'\n",
        encoding="utf-8",
    )

    (tmp_path / ".venv" / "lib" / "site-packages" / "pkg.py").write_text(
        "def venv_function():\n"
        "    return 'venv'\n",
        encoding="utf-8",
    )

    (tmp_path / "node_modules" / "lib.js").write_text(
        "export const x = 1;\n",
        encoding="utf-8",
    )

    return DummyProject(tmp_path)


@pytest.fixture
def patch_config(monkeypatch):
    """
    Patch get_config() in tool modules so excluded_dirs is defined
    without requiring external config files.
    """

    config = SimpleNamespace(
        security=SimpleNamespace(
            excluded_dirs=[".venv", "node_modules", ".git"],
        )
    )

    monkeypatch.setattr(
        "mcp_server_tree_sitter.tools.file_operations.get_config",
        lambda: config,
    )

    monkeypatch.setattr(
        "mcp_server_tree_sitter.tools.search.get_config",
        lambda: config,
    )

    monkeypatch.setattr(
        "mcp_server_tree_sitter.tools.analysis.get_config",
        lambda: config,
    )

    return config


def test_list_project_files_skips_excluded_dirs(sample_project, patch_config):
    """
    Ensure list_project_files() does not return files from excluded directories.
    """

    files = list_project_files(sample_project, pattern="**/*.py")

    assert "src/app.py" in files
    assert "src/other.py" in files

    # Ensure excluded directories are not listed
    assert all(not f.startswith(".venv/") for f in files)
    assert all("node_modules/" not in f for f in files)


def test_search_text_skips_excluded_dirs(sample_project, patch_config):
    """
    Ensure search_text() does not return matches from excluded directories.
    """

    results = search_text(
        project=sample_project,
        query="venv_function",
        file_pattern="**/*.py",
        case_sensitive=True,
    )

    if not results:
        return

    serialized = str(results)

    assert ".venv" not in serialized
    assert "node_modules" not in serialized


def test_search_text_finds_non_excluded_files(sample_project, patch_config):
    """
    Ensure search still works for non-excluded directories.
    """

    results = search_text(
        project=sample_project,
        query="public_function",
        file_pattern="**/*.py",
        case_sensitive=True,
    )

    assert results, "Expected search results in src/app.py"

    serialized = str(results)

    assert "src/app.py" in serialized
    assert ".venv" not in serialized


def test_analyze_project_structure_skips_excluded_dirs(sample_project, patch_config):
    """
    Ensure project structure analysis does not traverse excluded directories.
    """

    result = analyze_project_structure(
        project=sample_project,
        scan_depth=10,
    )

    serialized = str(result)

    assert ".venv" not in serialized
    assert "node_modules" not in serialized

    # Ensure normal project structure is still detected
    assert "src" in serialized
