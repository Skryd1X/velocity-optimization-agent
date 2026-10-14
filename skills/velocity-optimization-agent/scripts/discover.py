"""Bounded, read-only architecture signals. Signals are hypotheses, not coverage."""

import argparse
import json
import os
from pathlib import Path
from common import save

SKIP = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "vendor",
    "dist",
    "build",
    ".next",
    "Pods",
    "__pycache__",
}


def discover(root, limit=12000):
    root = Path(root).resolve(strict=True)
    signals = []
    manifests = []
    count = 0
    capped = False

    def add(platform, evidence):
        signals.append({"platform": platform, "evidence": evidence})

    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(
            d for d in dirs if d not in SKIP and not (Path(base) / d).is_symlink()
        )
        for name in sorted(files):
            count += 1
            if count > limit:
                capped = True
                break
            p = Path(base) / name
            if p.is_symlink():
                continue
            rel = p.relative_to(root).as_posix()
            if name == "package.json" and p.stat().st_size < 1048576:
                manifests.append(rel)
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    deps = set(data.get("dependencies", {})) | set(
                        data.get("devDependencies", {})
                    )
                except (ValueError, OSError):
                    add("unknown", "Unreadable manifest: " + rel)
                    continue
                for names, platform in [
                    ({"next", "react", "vue", "svelte", "astro"}, "web"),
                    ({"react-native", "expo"}, "native-mobile"),
                    ({"electron", "@tauri-apps/api"}, "desktop"),
                    ({"@telegram-apps/sdk", "@tma.js/sdk"}, "telegram-mini-app"),
                    ({"express", "fastify", "nestjs", "@nestjs/core"}, "backend"),
                ]:
                    if deps & names:
                        add(platform, rel + ": " + ", ".join(sorted(deps & names)))
            if name in {
                "pyproject.toml",
                "requirements.txt",
                "go.mod",
                "Cargo.toml",
                "composer.json",
            }:
                manifests.append(rel)
                add("service-or-library", rel)
            if name == "pubspec.yaml":
                manifests.append(rel)
                add("flutter", rel)
            if name == "AndroidManifest.xml":
                add("android", rel)
            if name.endswith((".xcodeproj", ".swift")):
                add("apple-native", rel)
            if name in {"app.json", "project.config.json"}:
                add("mini-app-or-mobile-config", rel)
        if capped:
            break
    return dict(
        schema_version=1,
        root=str(root),
        files_seen=min(count, limit),
        truncated=capped,
        excluded_directories=sorted(SKIP),
        signals=signals,
        manifests=manifests,
        coverage="manifest signals only; confirm routes, services and runtime",
    )


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("root")
    a.add_argument("--output", required=True)
    a.add_argument("--limit", type=int, default=12000)
    x = a.parse_args()
    if not 1 <= x.limit <= 100000:
        a.error("limit must be 1..100000")
    save(x.output, discover(x.root, x.limit))
