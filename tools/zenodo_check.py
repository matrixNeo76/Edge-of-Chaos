"""
zenodo_check.py
===============
Check the latest published version of each Zenodo record of the corpus against the local files
and the expected metadata. Read-only, public API, no token.

For each record in the configuration (tools/zenodo_records.toml):
- the latest version contains the expected file, with the MD5 of the local copy;
- the description contains the expected version note (e.g. "Version 6");
- the record belongs to the expected community;
- the expected related identifiers are present;
- for software, the version field matches.

Usage
    python -m tools.zenodo_check --config tools/zenodo_records.toml --docs-dir docs
"""

import argparse
import json
import re
import sys
import tomllib
import urllib.error
from pathlib import Path

from tools.build_papers import md5_of
from tools.verify_citations import http_get


def fetch_latest(concept_id, get=http_get):
    return json.loads(get(f"https://zenodo.org/api/records/{concept_id}/versions/latest"))


def check_record(spec, record, docs_dir=None, community=None):
    """Problems found in one record (empty list: consistent)."""
    problems = []
    metadata = record.get("metadata", {})
    files = {f["key"]: f.get("checksum", "").removeprefix("md5:") for f in record.get("files", [])}

    expected_file = spec.get("file")
    if expected_file:
        if expected_file not in files:
            problems.append(f"file '{expected_file}' not in the latest version (files: {sorted(files)})")
        elif docs_dir is None:
            problems.append("MD5 not compared: --docs-dir not given")
        else:
            local = docs_dir / expected_file
            if not local.exists():
                problems.append(f"local file {local} not found")
            elif md5_of(local) != files[expected_file]:
                problems.append(f"MD5 differs: Zenodo {files[expected_file]}, local {md5_of(local)}")

    note = spec.get("version_note")
    if note:
        description = re.sub(r"<[^>]+>", " ", metadata.get("description", ""))
        if note not in description:
            problems.append(f"version note '{note}' not in the description")

    version = spec.get("version")
    if version and metadata.get("version") != version:
        problems.append(f"version is {metadata.get('version')!r}, expected {version!r}")

    if community:
        communities = {c.get("id") for c in metadata.get("communities") or []}
        if community not in communities:
            problems.append(f"not in the community '{community}' (communities: {sorted(c for c in communities if c)})")

    related = {r.get("identifier") for r in metadata.get("related_identifiers") or []}
    for identifier in spec.get("related", []):
        if identifier not in related:
            problems.append(f"related identifier {identifier} missing")
    return problems


def run(config, docs_dir=None, get=http_get):
    community = config.get("community")
    results = []
    for spec in config.get("record", []):
        try:
            record = fetch_latest(spec["concept"], get=get)
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as error:
            results.append({"name": spec["name"], "record": None, "problems": [f"cannot read the record: {error}"]})
            continue
        try:
            problems = check_record(spec, record, docs_dir, community)
        except OSError as error:  # e.g. a local file that cannot be read
            problems = [f"cannot check the record: {error}"]
        results.append({"name": spec["name"], "record": record.get("id"), "problems": problems})
    return results


def report(results):
    lines = ["# Zenodo check", "", "| Record | Latest version | Status |", "|---|---|---|"]
    for r in results:
        status = "ok" if not r["problems"] else "; ".join(r["problems"])
        lines.append(f"| {r['name']} | {r['record']} | {status} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check the Zenodo records of the corpus.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--docs-dir", type=Path, help="directory of the local files, to compare MD5 checksums")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)

    config = tomllib.loads(args.config.read_text(encoding="utf-8"))
    results = run(config, args.docs_dir)
    text = report(results)
    if args.report:
        args.report.write_text(text, encoding="utf-8")
    print(text)
    return 1 if any(r["problems"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
