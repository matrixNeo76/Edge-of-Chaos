"""
check_versions.py
=================
The release version must be the same in Cargo.toml, Cargo.lock (package thermodynamic_valence),
CITATION.cff and .zenodo.json (the "vX.Y.Z" at the start of the notes), and it must have a
released section in CHANGELOG.md. Run in CI; exits 1 on a mismatch.

Usage
    python tools/check_versions.py [--repo-root .]
"""

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

PACKAGE = "thermodynamic_valence"


def read_versions(root):
    versions = {}
    cargo = tomllib.loads((root / "Cargo.toml").read_text(encoding="utf-8"))
    versions["Cargo.toml"] = cargo["package"]["version"]
    lock = tomllib.loads((root / "Cargo.lock").read_text(encoding="utf-8"))
    versions["Cargo.lock"] = next((p["version"] for p in lock.get("package", []) if p["name"] == PACKAGE), None)
    citation = re.search(r"^version:\s*['\"]?([\w.\-]+)", (root / "CITATION.cff").read_text(encoding="utf-8"), re.M)
    versions["CITATION.cff"] = citation.group(1) if citation else None
    notes = json.loads((root / ".zenodo.json").read_text(encoding="utf-8")).get("notes", "")
    zenodo = re.match(r"v(\d+\.\d+\.\d+)", notes)
    versions[".zenodo.json (notes)"] = zenodo.group(1) if zenodo else None
    return versions


def released_versions(changelog_text):
    return set(re.findall(r"^## \[(\d+\.\d+\.\d+)\]", changelog_text, re.M))


def check(root):
    versions = read_versions(root)
    problems = []
    distinct = set(versions.values())
    if len(distinct) != 1 or None in distinct:
        problems.append("versions disagree: " + ", ".join(f"{k}={v}" for k, v in versions.items()))
    version = versions["Cargo.toml"]
    if version not in released_versions((root / "CHANGELOG.md").read_text(encoding="utf-8")):
        problems.append(f"CHANGELOG.md has no released section for {version}")
    return version, problems


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check that the release version is consistent.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    version, problems = check(args.repo_root)
    for problem in problems:
        print(f"error: {problem}")
    if not problems:
        print(f"version {version} is consistent")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
