"""
public_guard.py
===============
Text that must not reach the public repository: the internal name of the entry-point paper, the
author's employer, names of confidential files. The rules, with their reasons and the paths where a
match is legitimate, are in tools/public_guard.toml.

It checks the files tracked by Git (or the paths given on the command line, e.g. by a pre-commit
hook) and exits 1 on any match. Binary files are skipped. Run in CI and as a local hook.

Usage
    python -m tools.public_guard [--config tools/public_guard.toml] [paths ...]
"""

import argparse
import fnmatch
import re
import subprocess
import sys
import tomllib
from pathlib import Path

CONFIG = Path("tools/public_guard.toml")
# The guard's own configuration and tests necessarily contain the patterns.
SELF = {"tools/public_guard.toml", "tools/public_guard.py", "tools/tests/test_public_guard.py"}


def load_rules(config_path):
    rules = tomllib.loads(Path(config_path).read_text(encoding="utf-8"))["rule"]
    return [(r["name"], re.compile(r["pattern"], re.IGNORECASE), r["reason"], r.get("allowed", [])) for r in rules]


def tracked_files(root):
    out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line]


def scan(root, paths, rules):
    """(path, line, rule name, reason) for every forbidden match outside the allowed paths."""
    findings = []
    for rel in paths:
        rel = rel.replace("\\", "/")
        if rel in SELF:
            continue
        try:
            text = (Path(root) / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue  # binary, deleted or not a file
        for name, pattern, reason, allowed in rules:
            if any(fnmatch.fnmatch(rel, glob) for glob in allowed):
                continue
            for number, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    findings.append((rel, number, name, reason))
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("paths", nargs="*", help="files to check (default: all files tracked by Git)")
    args = parser.parse_args(argv)
    rules = load_rules(args.repo_root / args.config if not args.config.is_absolute() else args.config)
    paths = args.paths or tracked_files(args.repo_root)
    findings = scan(args.repo_root, paths, rules)
    for rel, number, name, reason in findings:
        print(f"{rel}:{number}: {name}. {reason}")
    print(f"public_guard: {len(paths)} file(s) checked, {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
