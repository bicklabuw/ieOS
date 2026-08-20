# gui/utils/durable_io.py
"""Helpers for file writes that must survive sudden power loss."""

from __future__ import annotations

import json
import os
import shutil
from typing import Any


def _directory_for(path: str | os.PathLike[str]) -> str:
    directory = os.path.dirname(os.fspath(path))
    return directory or "."


def fsync_file(path: str | os.PathLike[str]) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def fsync_directory(path: str | os.PathLike[str]) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_text_atomic(path: str | os.PathLike[str], body: str, *, encoding: str = "utf-8") -> None:
    target = os.fspath(path)
    directory = _directory_for(target)
    os.makedirs(directory, mode=0o755, exist_ok=True)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding=encoding) as f:
        f.write(body)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, target)
    fsync_directory(directory)


def write_json_atomic(path: str | os.PathLike[str], payload: Any) -> None:
    write_text_atomic(path, json.dumps(payload, indent=2) + "\n")


def copy_file_durable(src: str | os.PathLike[str], dest: str | os.PathLike[str]) -> None:
    target = os.fspath(dest)
    directory = _directory_for(target)
    os.makedirs(directory, mode=0o755, exist_ok=True)
    shutil.copy2(src, target)
    fsync_file(target)
    fsync_directory(directory)


def fsync_tree(path: str | os.PathLike[str]) -> None:
    root = os.fspath(path)
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            fsync_file(os.path.join(dirpath, filename))
    for dirpath, dirnames, _ in os.walk(root, topdown=False):
        for dirname in dirnames:
            fsync_directory(os.path.join(dirpath, dirname))
        fsync_directory(dirpath)
