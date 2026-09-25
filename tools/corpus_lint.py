"""
corpus_lint.py
==============
Consistency checks for the LaTeX papers of the corpus. It reports; it never edits.

Errors (exit code 1):
- citations used but not defined in the paper's bibliography;
- revision numbers that disagree between the running header (\\lhead "rev. N"), the date
  ("revision N") and the highest "revision N" mentioned in the body;
- "facts" shared across papers (tools/corpus_facts.toml) that take a value not allowed there,
  e.g. a count of negative controls or a range of control numbers;
- rows of the theory-to-code map in PERSONA.md whose file or function does not exist.

Warnings:
- bibliography entries never cited;
- American spellings (the corpus uses British spelling; see PERSONA.md);
- expressions on the avoid-list of PERSONA.md;
- "P0_Distilled" in the text (never used externally for P0).

The bibliography (after \\begin{thebibliography}) is excluded from the text checks, so the
titles of cited works keep their own spelling.

Usage
    python tools/corpus_lint.py --docs-dir docs --facts tools/corpus_facts.toml --persona PERSONA.md
"""

import argparse
import re
import sys
import tomllib
from pathlib import Path

from tools.build_papers import DEFAULT_PAPERS

BS = "\\"
CITE = re.compile(re.escape(BS) + r"cite[a-zA-Z]*\*?(?:\[[^\]]*\]){0,2}\{([^}]*)\}")
BIBITEM = re.compile(re.escape(BS) + r"bibitem(?:\[[^\]]*\])?\{([^}]*)\}")
BIBLIOGRAPHY = BS + "begin{thebibliography}"
AMERICAN = re.compile(
    r"\b(organiz\w*|behavior\w*|modeling|modeled|analyz\w*|centers?|centered|colors?|favor\w*|labeled|labeling"
    r"|defense|recogniz\w*|characteriz\w*|generaliz\w*|normaliz\w*|realiz\w*|minimiz\w*|maximiz\w*|emphasiz\w*"
    r"|stabiliz\w*|optimiz\w*|summariz\w*|formaliz\w*|utiliz\w*|operationaliz\w*|conceptualiz\w*|categoriz\w*)\b",
    re.I)
# "horizon" alone is a technical term in the corpus (reference horizon, operational horizon);
# only its metaphorical uses are on the avoid-list.
AVOID = ["moreover, it is important to note", "in summary", "it is worth noting", "in conclusion, we can say",
         "revolutionary", "groundbreaking", "crucial", "cutting-edge", "landscape", "ecosystem",
         "on the horizon", "new horizons", "journey", "tapestry", "delve", "may potentially"]


def strip_comments(text):
    """Remove LaTeX comments (unescaped %) while keeping line numbers."""
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in text.split("\n"))


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def split_bibliography(text):
    position = text.find(BIBLIOGRAPHY)
    return (text, "") if position < 0 else (text[:position], text[position:])


def check_citations(body, bibliography):
    cited = {}
    for match in CITE.finditer(body):
        for key in (k.strip() for k in match.group(1).split(",")):
            if key:
                cited.setdefault(key, line_of(body, match.start()))
    defined = {m.group(1).strip() for m in BIBITEM.finditer(bibliography)}
    undefined = [(line, key) for key, line in sorted(cited.items(), key=lambda kv: kv[1]) if key not in defined]
    unused = sorted(defined - set(cited))
    return undefined, unused


def check_revisions(text):
    """Revision in the header, in the date and the highest one mentioned in the body must agree."""
    found = {}
    header = re.search(re.escape(BS + "lhead{") + r"[^}]*?rev\.~?\s*(\d+)", text)
    date = re.search(re.escape(BS + "date{") + r"[^}]*?revision\s+(\d+)", text)
    if header:
        found["header"] = int(header.group(1))
    if date:
        found["date"] = int(date.group(1))
    body = [int(n) for n in re.findall(r"[Rr]evision~?\s*(\d+)", text)]
    if body:
        found["body (highest)"] = max(body)
    return found if len(set(found.values())) > 1 else {}


def check_facts(name, body, facts):
    problems = []
    for fact in facts:
        if fact.get("files") and name not in fact["files"]:
            continue
        allowed = {str(v).lower() for v in fact["allowed"]}
        for match in re.finditer(fact["pattern"], body, re.I):
            value = match.group(1).lower()
            if value not in allowed:
                problems.append((line_of(body, match.start()), fact["name"], match.group(0), sorted(allowed)))
    return problems


def check_style(body):
    american = [(line_of(body, m.start()), m.group(0)) for m in AMERICAN.finditer(body)]
    lower = body.lower()
    avoid = []
    for phrase in AVOID:
        for match in re.finditer(r"\b" + re.escape(phrase) + r"\w*", lower):
            avoid.append((line_of(body, match.start()), body[match.start():match.end()]))
    distilled = [line_of(body, m.start()) for m in re.finditer(r"P0\\?_Distilled", body)]
    return american, sorted(avoid), distilled


def parse_persona_map(persona_text):
    """Implementation column of the theory-to-code table in PERSONA.md."""
    section = persona_text.split("Theory → code map", 1)
    if len(section) < 2:
        return []
    entries = []
    for line in section[1].split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and "`" in cells[1]:
            entries.extend(re.findall(r"`([^`]+)`", cells[1]))
    return entries


def check_persona_map(entries, repo_root):
    """Each entry is a file (a.py, a.py/.rs), a module.function, or a bare function name."""
    python_sources = {p: p.read_text(encoding="utf-8", errors="replace") for p in repo_root.glob("*.py")}
    missing = []
    for entry in entries:
        if "/" in entry:  # thermodynamic_valence.py/.rs
            stem, first_ext = entry.split("/")[0].rsplit(".", 1)
            extensions = [first_ext] + [e.lstrip(".") for e in entry.split("/")[1:]]
            if not all((repo_root / f"{stem}.{ext}").exists() for ext in extensions):
                missing.append(entry)
        elif entry.endswith((".py", ".rs")):
            if not (repo_root / entry).exists():
                missing.append(entry)
        elif "." in entry:  # module.function
            module, function = entry.rsplit(".", 1)
            source = repo_root / f"{module}.py"
            if not source.exists() or not re.search(rf"^def {re.escape(function)}\b", source.read_text(encoding="utf-8"), re.M):
                missing.append(entry)
        elif not any(re.search(rf"^def {re.escape(entry)}\b", s, re.M) for s in python_sources.values()):
            missing.append(entry)
    return missing


def lint(docs_dir, papers, facts, persona_path=None, repo_root=None):
    """Returns (errors, warnings) as lists of strings."""
    errors, warnings = [], []
    for name in papers:
        path = docs_dir / f"{name}.tex"
        if not path.exists():
            errors.append(f"{name}: file not found")
            continue
        text = strip_comments(path.read_text(encoding="utf-8"))
        body, bibliography = split_bibliography(text)
        undefined, unused = check_citations(body, bibliography)
        errors += [f"{name}:{line}: citation '{key}' is not in the bibliography" for line, key in undefined]
        warnings += [f"{name}: bibliography entry '{key}' is never cited" for key in unused]
        mismatch = check_revisions(text)
        if mismatch:
            errors.append(f"{name}: revision numbers disagree: {mismatch}")
        errors += [f"{name}:{line}: {fact}: '{found}' not in {allowed}"
                   for line, fact, found, allowed in check_facts(name, body, facts)]
        american, avoid, distilled = check_style(body)
        warnings += [f"{name}:{line}: American spelling '{word}'" for line, word in american]
        warnings += [f"{name}:{line}: avoid-list expression '{phrase}'" for line, phrase in avoid]
        warnings += [f"{name}:{line}: 'P0_Distilled' in the text" for line in distilled]
    if persona_path is not None and persona_path.exists():
        entries = parse_persona_map(persona_path.read_text(encoding="utf-8"))
        if not entries:
            errors.append(f"{persona_path.name}: theory-to-code map not found")
        errors += [f"{persona_path.name}: theory-to-code map entry '{e}' does not exist in the repository"
                   for e in check_persona_map(entries, repo_root or persona_path.parent)]
    return errors, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description="Consistency checks for the corpus papers.")
    parser.add_argument("--docs-dir", required=True, type=Path)
    parser.add_argument("--papers", nargs="+", default=DEFAULT_PAPERS)
    parser.add_argument("--facts", type=Path, help="TOML file of shared facts (default: none)")
    parser.add_argument("--persona", type=Path, help="PERSONA.md, to check the theory-to-code map")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)

    facts = tomllib.loads(args.facts.read_text(encoding="utf-8")).get("fact", []) if args.facts else []
    errors, warnings = lint(args.docs_dir, args.papers, facts, args.persona, args.repo_root)
    report = "# Corpus lint\n\n## Errors\n" + ("".join(f"- {e}\n" for e in errors) or "- none\n")
    report += "\n## Warnings\n" + ("".join(f"- {w}\n" for w in warnings) or "- none\n")
    if args.report:
        args.report.write_text(report, encoding="utf-8")
    print(report)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
