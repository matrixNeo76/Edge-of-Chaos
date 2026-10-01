"""
round.py
========
One command per phase of a revision round of the corpus, so that no step is skipped and the
results of every tool end up in one report.

    pre    before writing the spec: corpus_lint and verify_citations
    build  after the approved texts are applied: build_papers (backup, reproducible build, MD5)
    post   after the new versions are published: zenodo_check, then the knowledge graph:
           sync of its corpus and the number of files that changed since the last graph build

Each phase runs the existing tools as subprocesses with their usual options, collects their
Markdown reports in one file and exits 1 if any tool reported an error. The graph itself is
updated with graphify (an LLM extraction) and docs_v0.2/graph/postprocess.py; this command only
says whether that is needed, it does not run the extraction.

Usage
    python -m tools.round pre   [--report round.md]
    python -m tools.round build --backup-suffix _pre_round6 [--report round.md]
    python -m tools.round post  [--report round.md]
"""

import argparse
import datetime
import json
import subprocess
import sys
import tempfile
from pathlib import Path

DOCS = Path("docs")
WORK = Path("docs_v0.2")
GRAPH = WORK / "graph"


def run_tool(module, args, tmp):
    """Run python -m tools.<module> with --report; return (exit code, report text, stdout tail)."""
    report = Path(tmp) / f"{module}.md"
    cmd = [sys.executable, "-m", f"tools.{module}", *args, "--report", str(report)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    text = report.read_text(encoding="utf-8") if report.exists() else ""
    tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-5:])
    return proc.returncode, text, tail


def phase_pre(tmp):
    return [
        ("corpus_lint", run_tool("corpus_lint", ["--docs-dir", str(DOCS), "--facts", "tools/corpus_facts.toml",
                                                 "--persona", "PERSONA.md"], tmp)),
        ("verify_citations", run_tool("verify_citations", ["--docs-dir", str(DOCS), "--bib", "references.bib",
                                                           "--cache", str(WORK / ".citation_cache.json"),
                                                           "--accepted", "tools/citation_accepted.toml"], tmp)),
    ]


def phase_build(tmp, backup_suffix):
    args = ["--docs-dir", str(DOCS)] + (["--backup-suffix", backup_suffix] if backup_suffix else [])
    return [("build_papers", run_tool("build_papers", args, tmp))]


def graph_status():
    """Sync the graph corpus and count the files that changed since the last graph build."""
    if not (GRAPH / "sync_corpus.sh").exists():
        return 0, "", "no knowledge graph in this checkout"
    sync = subprocess.run(["bash", (GRAPH / "sync_corpus.sh").as_posix()], capture_output=True, text=True)
    if sync.returncode != 0:
        return 1, "", f"sync_corpus.sh failed: {sync.stderr.strip()[-300:]}"
    interpreter = GRAPH / "graphify-out" / ".graphify_python"
    if not interpreter.exists():
        return 0, "", f"{sync.stdout.strip()}; graphify not installed, change count unavailable"
    code = ("import json; from pathlib import Path; from graphify.detect import detect_incremental; "
            "r = detect_incremental(Path('corpus')); "
            "print(json.dumps({'new': r.get('new_total', 0), 'deleted': len(r.get('deleted_files', []))}))")
    probe = subprocess.run([interpreter.read_text(encoding="utf-8").strip(), "-c", code], cwd=GRAPH,
                           capture_output=True, text=True)
    try:
        counts = json.loads(probe.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return 0, "", f"{sync.stdout.strip()}; change count unavailable"
    if counts["new"] or counts["deleted"]:
        text = (f"{counts['new']} file(s) changed and {counts['deleted']} deleted since the last graph build. "
                "Update the graph: `/graphify docs_v0.2/graph/corpus --update`, then "
                "`postprocess.py` from docs_v0.2/graph, then republish the graph artifact.")
    else:
        text = "The knowledge graph is up to date."
    return 0, text, sync.stdout.strip()


def phase_post(tmp):
    results = [("zenodo_check", run_tool("zenodo_check", ["--config", "tools/zenodo_records.toml",
                                                          "--docs-dir", str(DOCS)], tmp))]
    results.append(("knowledge graph", graph_status()))
    return results


def combine(phase, results):
    lines = [f"# Revision round: {phase}", "", f"Run on {datetime.date.today().isoformat()}.", "",
             "| Step | Result |", "|---|---|"]
    for name, (code, _, _) in results:
        lines.append(f"| {name} | {'ok' if code == 0 else 'errors'} |")
    for name, (_, text, tail) in results:
        lines += ["", f"## {name}", ""]
        lines.append(text.strip() if text.strip() else f"```\n{tail}\n```")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("phase", choices=["pre", "build", "post"])
    parser.add_argument("--backup-suffix", help="for build: suffix of the backup folder, e.g. _pre_round6")
    parser.add_argument("--report", type=Path, help="write the combined report here (default: print it)")
    args = parser.parse_args(argv)
    if not DOCS.exists():
        print("docs/ not found: run from the repository root of a checkout with the corpus")
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        if args.phase == "pre":
            results = phase_pre(tmp)
        elif args.phase == "build":
            results = phase_build(tmp, args.backup_suffix)
        else:
            results = phase_post(tmp)
        text = combine(args.phase, results)
    if args.report:
        args.report.write_text(text, encoding="utf-8")
        print(f"report written to {args.report}")
    else:
        print(text)
    for name, (code, _, _) in results:
        print(f"{name}: {'ok' if code == 0 else 'errors'}")
    return 1 if any(code for _, (code, _, _) in results) else 0


if __name__ == "__main__":
    sys.exit(main())
