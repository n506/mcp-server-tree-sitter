from pathlib import Path

from mcp_server_tree_sitter.utils.path import iter_project_files_pruned


def test_iter_project_files_pruned_excludes_directories(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / ".venv" / "lib").mkdir(parents=True)
    (tmp_path / "node_modules").mkdir()

    (tmp_path / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / ".venv" / "lib" / "bad.py").write_text("print('bad')\n", encoding="utf-8")
    (tmp_path / "node_modules" / "mod.js").write_text("x=1\n", encoding="utf-8")

    files = [
        p.relative_to(tmp_path).as_posix()
        for p in iter_project_files_pruned(
            tmp_path,
            "**/*",
            excluded_dirs=[".venv", "node_modules"],
        )
    ]

    assert "src/app.py" in files
    assert ".venv/lib/bad.py" not in files
    assert "node_modules/mod.js" not in files


def test_iter_project_files_pruned_respects_pattern(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / ".venv" / "lib").mkdir(parents=True)

    (tmp_path / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "src" / "note.txt").write_text("hello\n", encoding="utf-8")
    (tmp_path / ".venv" / "lib" / "bad.py").write_text("print('bad')\n", encoding="utf-8")

    py_files = [
        p.relative_to(tmp_path).as_posix()
        for p in iter_project_files_pruned(
            tmp_path,
            "**/*.py",
            excluded_dirs=[".venv"],
        )
    ]

    assert py_files == ["src/app.py"]
