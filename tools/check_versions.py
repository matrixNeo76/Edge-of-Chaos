"""
check_versions.py
=================
The release version must be the same in Cargo.toml, Cargo.lock (package thermodynamic_valence),
CITATION.cff and .zenodo.json (the "vX.Y.Z" at the start of the notes), and it must have a
released section in CHANGELOG.md. The citation metadata must also agree where both files state
it: title, author ORCID, and a .zenodo.json licence that is one of the licences of the software
(Zenodo reads .zenodo.json and ignores CITATION.cff when both exist). Run in CI; exits 1 on a
mismatch.

Usage
    python -m tools.check_versions [--repo-root .]
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
    zenodo = re.match(r"v(\d+\.\d+\.\d+)(?=\s|$)", notes)  # "v0.4.01" is not 0.4.0
    versions[".zenodo.json (notes)"] = zenodo.group(1) if zenodo else None
    return versions


def released_versions(changelog_text):
    return set(re.findall(r"^## \[(\d+\.\d+\.\d+)\]", changelog_text, re.M))


def citation_metadata(root):
    """Title, ORCIDs and licences stated by CITATION.cff, .zenodo.json and Cargo.toml (None if absent)."""
    cff = (root / "CITATION.cff").read_text(encoding="utf-8")
    zen = json.loads((root / ".zenodo.json").read_text(encoding="utf-8"))
    cargo = tomllib.loads((root / "Cargo.toml").read_text(encoding="utf-8"))["package"]
    title = re.search(r"^title:\s*['\"]?(.+?)['\"]?\s*$", cff, re.M)
    # "license: MIT" on one line, or "license:" followed by an indented list of identifiers
    block = re.search(r"^license:[ \t]*(\S.*)?\n((?:[ \t]+-[ \t]*\S.*\n?)*)", cff, re.M)
    cff_licences = set()
    if block:
        cff_licences = {block.group(1).strip()} if block.group(1) else set(re.findall(r"-[ \t]*(\S+)", block.group(2)))
    return {
        "cff_title": title.group(1) if title else None,
        "zenodo_title": zen.get("title"),
        "cff_orcids": {o.rsplit("/", 1)[-1] for o in re.findall(r"orcid:\s*['\"]?(\S+?)['\"]?$", cff, re.M)},
        "zenodo_orcids": {c["orcid"] for c in zen.get("creators", []) if c.get("orcid")},
        "licences": cff_licences | (set(re.split(r"\s+OR\s+", cargo.get("license", ""))) - {""}),
        "zenodo_licence": zen.get("license"),
    }


def check_metadata(root):
    meta, problems = citation_metadata(root), []
    if meta["cff_title"] and meta["zenodo_title"] and meta["cff_title"] != meta["zenodo_title"]:
        problems.append(f"title differs: CITATION.cff '{meta['cff_title']}', .zenodo.json '{meta['zenodo_title']}'")
    if meta["cff_orcids"] and meta["zenodo_orcids"] and meta["cff_orcids"] != meta["zenodo_orcids"]:
        problems.append(f"ORCIDs differ: CITATION.cff {sorted(meta['cff_orcids'])}, .zenodo.json {sorted(meta['zenodo_orcids'])}")
    if meta["zenodo_licence"] and meta["licences"] and meta["zenodo_licence"] not in meta["licences"]:
        problems.append(f".zenodo.json licence {meta['zenodo_licence']} is not one of {sorted(meta['licences'])}")
    return problems


def check(root):
    versions = read_versions(root)
    problems = []
    distinct = set(versions.values())
    if len(distinct) != 1 or None in distinct:
        problems.append("versions disagree: " + ", ".join(f"{k}={v}" for k, v in versions.items()))
    version = versions["Cargo.toml"]
    if version not in released_versions((root / "CHANGELOG.md").read_text(encoding="utf-8")):
        problems.append(f"CHANGELOG.md has no released section for {version}")
    problems += check_metadata(root)
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
