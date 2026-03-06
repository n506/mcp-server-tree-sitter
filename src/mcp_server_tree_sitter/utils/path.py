"""Path utilities for mcp-server-tree-sitter."""

import os
from pathlib import Path, PurePosixPath
from typing import Iterable, Union


def normalize_path(path: Union[str, Path], ensure_absolute: bool = False) -> Path:
    """
    Normalize a path for cross-platform compatibility.

    Args:
        path: Path string or object
        ensure_absolute: If True, raises ValueError for relative paths

    Returns:
        Normalized Path object
    """
    path_obj = Path(path).expanduser().resolve()

    if ensure_absolute and not path_obj.is_absolute():
        raise ValueError(f"Path must be absolute: {path}")

    return path_obj


def safe_relative_path(path: Union[str, Path], base: Union[str, Path]) -> Path:
    """
    Safely get a relative path that prevents directory traversal attacks.

    Args:
        path: Target path
        base: Base directory that should contain the path

    Returns:
        Relative path object

    Raises:
        ValueError: If path attempts to escape base directory
    """
    base_path = normalize_path(base)
    target_path = normalize_path(path)

    # Ensure target is within base
    try:
        relative = target_path.relative_to(base_path)
        # Check for directory traversal
        if ".." in str(relative).split(os.sep):
            raise ValueError(f"Path contains forbidden directory traversal: {path}")
        return relative
    except ValueError as e:
        raise ValueError(f"Path {path} is not within base directory {base}") from e


def get_project_root(path: Union[str, Path]) -> Path:
    """
    Attempt to determine project root from a file path by looking for common markers.

    Args:
        path: Path to start from (file or directory)

    Returns:
        Path to likely project root
    """
    path_obj = normalize_path(path)

    # If path is a file, start from its directory
    if path_obj.is_file():
        path_obj = path_obj.parent

    # Look for common project indicators
    markers = [
        ".git",
        "pyproject.toml",
        "setup.py",
        "package.json",
        "Cargo.toml",
        "CMakeLists.txt",
        ".svn",
        "Makefile",
    ]

    # Start from path and go up directories until a marker is found
    current = path_obj
    while current != current.parent:  # Stop at filesystem root
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent

    # If no marker found, return original directory
    return path_obj


def iter_project_files_pruned(
    root: Path,
    pattern: str,
    excluded_dirs: list[str] | set[str] | tuple[str, ...] | None = None,
) -> Iterable[Path]:
    """
    Yield files under `root` matching `pattern`, while never descending into
    directories listed in config.security.excluded_dirs.

    Matching is performed against the relative POSIX path using glob semantics.
    """
    excluded = set(excluded_dirs or [])
    normalized_pattern = (pattern or "**/*").replace("\\", "/")

    for current_dir, dirs, files in os.walk(root, topdown=True, followlinks=False):
        dirs[:] = [d for d in dirs if d not in excluded]

        current_path = Path(current_dir)
        for filename in files:
            file_path = current_path / filename
            rel_path = file_path.relative_to(root).as_posix()

            if PurePosixPath(rel_path).match(normalized_pattern):
                yield file_path
