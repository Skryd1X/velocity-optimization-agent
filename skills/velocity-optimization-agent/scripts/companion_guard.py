"""Pinned companion discovery and installation with an exclusive state lock."""

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from common import read

CATALOG = Path(__file__).resolve().parents[1] / "assets/companions.json"


def metadata(path, name):
    if (
        path.is_symlink()
        or any(p.is_symlink() for p in path.parents)
        or not (path / "SKILL.md").is_file()
        or (path / "SKILL.md").is_symlink()
    ):
        return False
    text = (path / "SKILL.md").read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---" not in text[4:]:
        return False
    front = text[4:].split("\n---", 1)[0]
    return bool(
        re.search(r"^name:\s*" + re.escape(name) + r"\s*$", front, re.M)
        and re.search(r'^\s+version:\s*["\']?1\.\d+\.\d+["\']?\s*$', front, re.M)
    )


def fetch(spec, destination):
    with tempfile.TemporaryDirectory(prefix="velocity-companion-") as folder:
        base = Path(folder)
        for args in [
            ("init",),
            ("remote", "add", "origin", spec["repository"]),
            ("fetch", "--depth=1", "origin", spec["ref"]),
            ("checkout", "--detach", "FETCH_HEAD"),
        ]:
            subprocess.run(
                ["git", "-c", "core.hooksPath=" + str(base / "disabled-hooks"), *args],
                cwd=base,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=180,
            )
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=base, text=True
        ).strip()
        if revision != spec["ref"]:
            raise ValueError("Fetched revision mismatch")
        source = base / spec["path"]
        if (
            source.is_symlink()
            or any(p.is_symlink() for p in source.parents)
            or any(p.is_symlink() for p in source.rglob("*"))
            or not source.is_dir()
        ):
            raise ValueError("Unsafe source")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if any(
            p.is_symlink() for p in [destination.parent, *destination.parent.parents]
        ):
            raise ValueError("Symlink destination refused")
        destination.mkdir(exist_ok=False)
        try:
            shutil.copytree(source, destination, dirs_exist_ok=True)
            if not metadata(destination, destination.name):
                raise ValueError("Incompatible installed metadata")
        except Exception:
            shutil.rmtree(destination)
            raise


def ensure(
    state,
    name,
    client,
    root,
    loaded=False,
    extra=None,
    include_user=True,
    allow_install=False,
    retry_key="initial",
    fetcher=fetch,
):
    specs = read(CATALOG)["companions"]
    if name not in specs or client not in ("codex", "claude"):
        raise ValueError("Unknown companion/client")
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Root must be an existing directory")
    roots = [root] + ([Path.home()] if include_user else [])
    candidates = [
        p / d / "skills" / name
        for p in roots
        for d in ((".agents", ".codex") if client == "codex" else (".claude",))
    ]
    if extra:
        candidates.insert(0, Path(extra).expanduser().absolute())
    entries = state.setdefault("companions", {})
    key = f"{client}:{root}:{name}"
    entry = entries.setdefault(key, {})
    for candidate in candidates:
        if candidate.exists() or candidate.is_symlink():
            status = (
                ("ready" if loaded else "needs-reload")
                if metadata(candidate, name)
                else "failed"
            )
            entry.update(
                status=status,
                path=str(candidate),
                reason="Existing installation reused"
                if status != "failed"
                else "Existing incompatible/unsafe installation; no overwrite",
            )
            return dict(entry, suggest_install=False)
    if not allow_install:
        first = not entry.get("offered")
        entry.update(status="missing", offered=True)
        return dict(entry, suggest_install=first)
    spec = specs[name]
    attempt = f"{spec['ref']}:{retry_key}"
    if entry.get("attempt") == attempt:
        return dict(entry, suggest_install=False)
    entry.update(attempt=attempt, status="installing")
    destination = (
        root / (".agents" if client == "codex" else ".claude") / "skills" / name
    )
    try:
        fetcher(spec, destination)
        entry.update(
            status="needs-reload",
            path=str(destination),
            repository=spec["repository"],
            ref=spec["ref"],
        )
    except Exception as exc:
        entry.update(status="failed", reason=type(exc).__name__)
    return dict(entry, suggest_install=False)


def claim(state, name, scope, revision, depth=1):
    if (
        name not in read(CATALOG)["companions"]
        or depth != 1
        or not scope
        or not revision
    ):
        raise ValueError(
            "Direct companion, scope and revision required; recursion refused"
        )
    if not any(
        key.endswith(":" + name) and item.get("status") == "ready"
        for key, item in state.get("companions", {}).items()
    ):
        return {"status": "companion-not-ready", "dispatch": False}
    key = json.dumps([name, scope, revision])
    tasks = state.setdefault("tasks", {})
    if key in tasks:
        return dict(tasks[key], dispatch=False, key=key)
    if any(t["status"] == "running" and t["scope"] == scope for t in tasks.values()):
        return {"status": "scope-busy", "dispatch": False, "key": key}
    tasks[key] = dict(name=name, scope=scope, revision=revision, status="running")
    return dict(tasks[key], dispatch=True, key=key)


def finish(state, key, status, evidence):
    if (
        status not in ("completed", "failed")
        or not evidence
        or key not in state.get("tasks", {})
    ):
        raise ValueError("Known task and evidence/reason required")
    state["tasks"][key].update(status=status, evidence=evidence)
    return state["tasks"][key]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--state", required=True)
    sub = p.add_subparsers(dest="command", required=True)
    e = sub.add_parser("ensure")
    e.add_argument("--name", required=True)
    e.add_argument("--client", choices=["codex", "claude"], required=True)
    e.add_argument("--root", required=True)
    e.add_argument("--loaded", action="store_true")
    e.add_argument("--path")
    e.add_argument("--include-user", action="store_true", default=True)
    e.add_argument("--project-only", action="store_true")
    e.add_argument("--allow-install", action="store_true")
    e.add_argument("--retry-key", default="initial")
    c = sub.add_parser("claim")
    c.add_argument("--name", required=True)
    c.add_argument("--scope", required=True)
    c.add_argument("--revision", required=True)
    c.add_argument("--depth", type=int, default=1)
    f = sub.add_parser("finish")
    f.add_argument("--key", required=True)
    f.add_argument("--status", choices=["completed", "failed"], required=True)
    f.add_argument("--evidence", nargs="+", required=True)
    a = p.parse_args()
    target = Path(a.state).absolute()
    target.parent.mkdir(parents=True, exist_ok=True)
    lock = target.with_suffix(target.suffix + ".lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        p.exit(3, "Registry busy; no work dispatched or installation attempted.\n")
    temp = None
    try:
        os.close(fd)
        state = read(target) if target.exists() else {"schema_version": 1}
        if a.command == "ensure":
            result = ensure(
                state,
                a.name,
                a.client,
                a.root,
                a.loaded,
                a.path,
                a.include_user and not a.project_only,
                a.allow_install,
                a.retry_key,
            )
        elif a.command == "claim":
            result = claim(state, a.name, a.scope, a.revision, a.depth)
        else:
            result = finish(state, a.key, a.status, a.evidence)
        handle, temp = tempfile.mkstemp(prefix=target.name + ".", dir=target.parent)
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            json.dump(state, out, indent=2)
            out.write("\n")
        os.replace(temp, target)
        temp = None
        print(json.dumps(result, indent=2))
    finally:
        if temp:
            Path(temp).unlink(missing_ok=True)
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
