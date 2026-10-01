"""pyproject.toml is the single source of the Python dependencies; requirements*.txt must not drift."""

import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def requirement_lines(path):
    """Requirement specifiers of a requirements file, without comments, blanks and -r includes."""
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line and not line.startswith("-r"):
            lines.append(line.replace(" ", ""))
    return sorted(lines)


class DependencySyncTest(unittest.TestCase):
    def setUp(self):
        self.pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    def test_runtime_dependencies_match(self):
        expected = sorted(d.replace(" ", "") for d in self.pyproject["project"]["dependencies"])
        self.assertEqual(requirement_lines(ROOT / "requirements.txt"), expected)

    def test_build_dependencies_match(self):
        expected = sorted(d.replace(" ", "") for d in self.pyproject["dependency-groups"]["build"])
        self.assertEqual(requirement_lines(ROOT / "requirements-dev.txt"), expected)


if __name__ == "__main__":
    unittest.main()
