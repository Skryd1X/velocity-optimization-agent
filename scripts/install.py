#!/usr/bin/env python3
"""Install reviewed local skill files without replacing existing installations."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

NAME = "velocity-optimization-agent"
SOURCE = Path(__file__).resolve().parents[1] / "skills" / NAME


def install(agent: str, base: Path, source: Path = SOURCE) -> list[Path]:
    """Preflight every destination before copying; never follow package symlinks."""
    if agent not in {"claude", "codex", "both"}:
        raise ValueError("Unsupported agent")
    base = base.expanduser().resolve(strict=True)
    if not base.is_dir():
        raise ValueError("Installation root must be an existing directory")
    if (
        not source.is_dir()
        or source.is_symlink()
        or not (source / "SKILL.md").is_file()
    ):
        raise ValueError("The canonical skill directory is missing or unsafe")
    if any(path.is_symlink() for path in source.rglob("*")):
        raise ValueError("Skill package must not contain symlinks")
    clients = ["codex", "claude"] if agent == "both" else [agent]
    destinations = [
        base / (".agents" if client == "codex" else ".claude") / "skills" / NAME
        for client in clients
    ]
    for destination in destinations:
        for parent in (destination.parent.parent, destination.parent):
            if parent.is_symlink():
                raise ValueError(f"Refusing symlinked installation path: {parent}")
            if parent.exists() and not parent.is_dir():
                raise ValueError(f"Installation path is not a directory: {parent}")
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f"Installation already exists: {destination}")
        if not destination.resolve().is_relative_to(base):
            raise ValueError("Installation path escapes the requested root")
    # Exclusive creation protects an existing installation even if it appears
    # after preflight. Roll back only directories created by this invocation.
    created: list[Path] = []
    try:
        for destination in destinations:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.mkdir(exist_ok=False)
            created.append(destination)
            shutil.copytree(
                source,
                destination,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
    except Exception:
        for destination in reversed(created):
            shutil.rmtree(destination)
        raise
    return destinations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", choices=("claude", "codex", "both"), required=True)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument(
        "--project", type=Path, help="Existing application repository directory"
    )
    scope.add_argument(
        "--user", action="store_true", help="Install under the user home directory"
    )
    args = parser.parse_args()
    try:
        destinations = install(args.agent, Path.home() if args.user else args.project)
    except (OSError, ValueError) as error:
        print(f"Installation failed: {error}", file=sys.stderr)
        return 1
    for destination in destinations:
        print(f"Installed: {destination}")
    print("Reload/restart the client if skill discovery has not refreshed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
