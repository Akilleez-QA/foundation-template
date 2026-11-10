import ast
import io
import tokenize
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("foundation_template", "foundation_template_bridge", "tools", "tests")


def python_sources():
    return sorted(path for package in PACKAGES for path in (ROOT / package).rglob("*.py")
                  if "__pycache__" not in path.parts)


def comments(source):
    return [token for token in tokenize.generate_tokens(io.StringIO(source).readline)
            if token.type == tokenize.COMMENT]


def docstrings(source):
    nodes = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    return [node for node in ast.walk(ast.parse(source)) if isinstance(node, nodes) and ast.get_docstring(node)]


class SourceRuleTests(unittest.TestCase):
    def test_python_sources_have_no_comments(self):
        self.assertTrue(python_sources())
        found = {str(path.relative_to(ROOT)): [token.start[0] for token in comments(path.read_text())]
                 for path in python_sources()}
        self.assertEqual({name: lines for name, lines in found.items() if lines}, {})

    def test_python_sources_have_no_docstrings(self):
        found = {str(path.relative_to(ROOT)): [getattr(node, "lineno", 1) for node in docstrings(path.read_text())]
                 for path in python_sources()}
        self.assertEqual({name: lines for name, lines in found.items() if lines}, {})

    def test_rule_detects_a_comment_and_a_docstring(self):
        self.assertEqual(len(comments("x = 1  # noqa: BLE001\n")), 1)
        self.assertEqual(comments("x = '# not a comment'\n"), [])
        self.assertEqual(len(docstrings('class A:\n    """Doc."""\n')), 1)
        self.assertEqual(docstrings("class A:\n    x = 'value'\n"), [])


if __name__ == "__main__":
    unittest.main()
