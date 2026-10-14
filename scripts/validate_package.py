from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / "skills/velocity-optimization-agent"
assert list(ROOT.rglob("SKILL.md")) == [S / "SKILL.md"], (
    "Exactly one active skill required"
)
text = (S / "SKILL.md").read_text(encoding="utf-8")
assert "name: velocity-optimization-agent" in text
lock = json.loads((S / "shared-tools.lock.json").read_text())
for entry in lock["files"]:
    p = S / entry["path"]
    assert hashlib.sha256(p.read_bytes()).hexdigest() == entry["sha256"], str(p)
assert len(json.loads((S / "assets/device-catalog.json").read_text())["devices"]) == 207
for p in ROOT.rglob("*.py"):
    compile(p.read_text(encoding="utf-8"), str(p), "exec")
for p in ROOT.rglob("*.json"):
    json.loads(p.read_text(encoding="utf-8"))
for p in [ROOT / "README.md", S / "SKILL.md", *S.glob("references/*.md")]:
    for link in re.findall(r"\[[^]]*\]\(([^)]+)\)", p.read_text(encoding="utf-8")):
        if not link.startswith(("http", "mailto:", "#")):
            assert (p.parent / link.split("#")[0]).exists(), (p, link)
print("Package structure, JSON, Python syntax and local document links passed")
