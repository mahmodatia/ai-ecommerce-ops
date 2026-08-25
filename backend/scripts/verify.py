from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent


def run(*args: str, cwd: Path = BACKEND):
    print("\n>", " ".join(args))
    result = subprocess.run(args, cwd=cwd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main():
    run(sys.executable, "-m", "compileall", "-q", "app", "scripts")
    run(sys.executable, "-m", "pytest", "-q")
    run(sys.executable, "scripts/evaluate.py")
    run(sys.executable, "scripts/release_check.py")

    js_files = sorted((ROOT / "frontend" / "js").rglob("*.js"))
    import_errors = []
    import_pattern = re.compile(r'from\s+["\']([^"\']+)["\']')
    for path in js_files:
        text = path.read_text(encoding="utf-8")
        for target in import_pattern.findall(text):
            if not target.startswith("."):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                import_errors.append(f"{path.relative_to(ROOT)} -> {target}")
    if import_errors:
        print("\nFrontend import graph FAILED")
        for item in import_errors:
            print("-", item)
        raise SystemExit(1)
    print(f"\nFrontend import graph: {len(js_files)} files PASSED")

    node = shutil.which("node")
    if node:
        for path in js_files:
            run(node, "--check", str(path), cwd=ROOT)
        print(f"\nFrontend JavaScript syntax: {len(js_files)} files PASSED")
    else:
        print("\nNode.js not found; frontend syntax check skipped locally (CI runs it).")

    print("\nVerification complete.")


if __name__ == "__main__":
    main()
