"""
build_papers.py
===============
Build and check the LaTeX papers of the corpus: back up, compile (three pdflatex passes),
check the sources and the logs, and write a table of pages, sizes and MD5 checksums ready for
the Zenodo upload notes. It never modifies a .tex file.

Checks
- sources: control characters (e.g. a TAB where a stray sed turned "\\citep" into "\\t" + "itep");
- logs: LaTeX errors, undefined citations and references, overfull boxes above a threshold,
  split into those already recorded in a baseline and new ones.

Reproducible PDFs: pdfTeX embeds the build time. With SOURCE_DATE_EPOCH and FORCE_SOURCE_DATE=1
it uses a fixed time instead, so the same source gives byte-identical PDFs (same MD5), in any
directory. The epoch defaults to the modification time of the .tex file; pass --epoch to build a
copy (e.g. the arXiv package) identical to the original.

Usage
    python tools/build_papers.py --docs-dir docs --backup-suffix _pre_round4
    python tools/build_papers.py --docs-dir docs --no-build        # checks on existing logs only
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_PAPERS = ["P0_Distilled_v0.1", "P1_Main", "P2_SelfAgency", "P3_Critique",
                  "C1_Philosophy", "C2_PowerAnalysis", "ES_Summary"]
OVERFULL_THRESHOLD_PT = 5.0
ALLOWED_CONTROL = {"\n", "\r"}


def find_control_characters(text):
    """(line, column, character name) for every control character other than newlines."""
    found = []
    for line_no, line in enumerate(text.split("\n"), start=1):
        for col, ch in enumerate(line, start=1):
            if ord(ch) < 32 and ch not in ALLOWED_CONTROL or ord(ch) == 127:
                found.append((line_no, col, f"U+{ord(ch):04X}"))
    return found


def parse_log(log_text, threshold=OVERFULL_THRESHOLD_PT):
    """Extract the build outcome from a pdflatex log."""
    output = re.search(r"Output written on .*?\((\d+) pages?, (\d+) bytes\)", log_text, re.S)
    undefined_citations = sorted(set(re.findall(r"Citation `([^']+)'.*?undefined", log_text)))
    undefined_references = sorted(set(re.findall(r"Reference `([^']+)'.*?undefined", log_text)))
    errors = re.findall(r"^! (.+)$", log_text, re.M)
    overfull = []
    for match in re.finditer(r"Overfull \\hbox \(([\d.]+)pt too wide\) (?:in paragraph |in alignment |detected )?at lines? ([\d-]+)",
                             log_text):
        width = float(match.group(1))
        if width > threshold:
            overfull.append({"width_pt": width, "lines": match.group(2)})
    return {
        "pages": int(output.group(1)) if output else None,
        "bytes": int(output.group(2)) if output else None,
        "undefined_citations": undefined_citations,
        "undefined_references": undefined_references,
        "errors": errors,
        "overfull": overfull,
    }


def split_overfull(overfull, baseline_lines):
    """Separate overfull boxes already recorded in the baseline (by source lines) from new ones."""
    known = set(baseline_lines)
    return ([o for o in overfull if o["lines"] in known], [o for o in overfull if o["lines"] not in known])


def md5_of(path):
    digest = hashlib.md5()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def zenodo_size(n_bytes):
    """Size as Zenodo shows it: decimal kilobytes (1 kB = 1000 bytes), one decimal."""
    return f"{n_bytes / 1000:.1f} kB"


def find_pdflatex(explicit=None):
    candidate = explicit or os.environ.get("PDFLATEX") or shutil.which("pdflatex")
    if not candidate:
        raise FileNotFoundError("pdflatex not found: add it to PATH, set PDFLATEX or pass --pdflatex")
    return candidate


def compile_paper(tex_path, pdflatex, epoch=None, passes=3):
    """Run pdflatex `passes` times in the file's directory; returns the log text."""
    env = dict(os.environ)
    if epoch is not None:
        env["SOURCE_DATE_EPOCH"] = str(int(epoch))
        env["FORCE_SOURCE_DATE"] = "1"
    for _ in range(passes):
        subprocess.run([pdflatex, "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
                       cwd=tex_path.parent, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       check=False)
    log = tex_path.with_suffix(".log")
    return log.read_text(encoding="latin-1") if log.exists() else ""


def backup(tex_path, backup_dir, suffix):
    backup_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".tex", ".pdf"):
        source = tex_path.with_suffix(ext)
        if source.exists():
            shutil.copy2(source, backup_dir / f"{tex_path.stem}{suffix}{ext}")


def build_report(results):
    lines = ["# Build report", "",
             "| Paper | Pages | Bytes | Zenodo size | MD5 | Status |",
             "|---|---|---|---|---|---|"]
    for r in results:
        status = "ok" if r["ok"] else "**CHECK**"
        lines.append(f"| {r['paper']} | {r['pages']} | {r['bytes']} | {r['zenodo_size']} | `{r['md5']}` | {status} |")
    for r in results:
        problems = []
        if r["control_characters"]:
            problems.append(f"control characters at {r['control_characters']}")
        if r["errors"]:
            problems.append(f"LaTeX errors: {r['errors']}")
        if r["undefined_citations"]:
            problems.append(f"undefined citations: {r['undefined_citations']}")
        if r["undefined_references"]:
            problems.append(f"undefined references: {r['undefined_references']}")
        if r["new_overfull"]:
            problems.append("new overfull boxes: " + ", ".join(f"{o['width_pt']}pt at lines {o['lines']}" for o in r["new_overfull"]))
        if problems:
            lines += ["", f"## {r['paper']}"] + [f"- {p}" for p in problems]
    if results and results[0].get("epoch") is not None:
        lines += ["", "Reproducible build: SOURCE_DATE_EPOCH per paper = "
                  + ", ".join(f"{r['paper']}={r['epoch']}" for r in results)]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--docs-dir", required=True, type=Path)
    parser.add_argument("--papers", nargs="+", default=DEFAULT_PAPERS, help="base names without .tex")
    parser.add_argument("--no-build", action="store_true", help="only check existing logs and PDFs")
    parser.add_argument("--backup-suffix", help="back up .tex/.pdf with this suffix before building")
    parser.add_argument("--backup-dir", type=Path, help="default: <docs-dir>/_pdf_backup_pre_v2")
    parser.add_argument("--epoch", type=int, help="SOURCE_DATE_EPOCH for all papers (default: .tex mtime)")
    parser.add_argument("--not-reproducible", action="store_true", help="embed the real build time")
    parser.add_argument("--pdflatex")
    parser.add_argument("--baseline", type=Path, help="JSON of known overfull boxes (default: <docs-dir>/.build_baseline.json)")
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--report", type=Path, help="write the Markdown report here")
    args = parser.parse_args(argv)

    docs = args.docs_dir
    baseline_path = args.baseline or docs / ".build_baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else {}
    pdflatex = None if args.no_build else find_pdflatex(args.pdflatex)

    results = []
    for name in args.papers:
        tex = docs / f"{name}.tex"
        if not tex.exists():
            print(f"missing: {tex}", file=sys.stderr)
            return 2
        if args.backup_suffix and not args.no_build:
            backup(tex, args.backup_dir or docs / "_pdf_backup_pre_v2", args.backup_suffix)
        epoch = None if args.not_reproducible else (args.epoch if args.epoch is not None else int(tex.stat().st_mtime))
        if args.no_build:
            log_path = tex.with_suffix(".log")
            log_text = log_path.read_text(encoding="latin-1") if log_path.exists() else ""
        else:
            log_text = compile_paper(tex, pdflatex, epoch=epoch)
        info = parse_log(log_text)
        known, new = split_overfull(info["overfull"], baseline.get(name, []))
        pdf = tex.with_suffix(".pdf")
        control = find_control_characters(tex.read_text(encoding="utf-8"))
        ok = pdf.exists() and info["pages"] is not None and not (control or info["errors"] or info["undefined_citations"]
                                                                   or info["undefined_references"] or new)
        results.append({
            "paper": name, "pages": info["pages"], "bytes": pdf.stat().st_size if pdf.exists() else None,
            "zenodo_size": zenodo_size(pdf.stat().st_size) if pdf.exists() else "-",
            "md5": md5_of(pdf) if pdf.exists() else "-", "control_characters": control,
            "errors": info["errors"], "undefined_citations": info["undefined_citations"],
            "undefined_references": info["undefined_references"], "known_overfull": known,
            "new_overfull": new, "epoch": epoch, "ok": ok,
        })
        if args.update_baseline:
            baseline[name] = [o["lines"] for o in info["overfull"]]

    if args.update_baseline:
        baseline_path.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    report = build_report(results)
    if args.report:
        args.report.write_text(report, encoding="utf-8")
    print(report)
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
