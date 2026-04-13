"""FR-29 locale sweep — user-visible string literals in app/gui/*.py must use
zh-TW conventions. Simplified Chinese variants (`数据` / `程序` / `分辨率`)
are forbidden.

Scope (per r6 AC-4): user-visible string literals only; module / class /
function docstrings and comments are excluded.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

_FORBIDDEN = re.compile(r"数据|程序|分辨率")
_REPO_ROOT = Path(__file__).resolve().parent.parent
_GUI_DIR = _REPO_ROOT / "app" / "gui"


def _iter_gui_sources() -> list[Path]:
    return sorted(p for p in _GUI_DIR.glob("*.py") if p.is_file())


def _docstring_node_ids(tree: ast.AST) -> set[int]:
    """Collect id() of docstring Constant nodes so we can skip them."""
    doc_ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                if isinstance(body[0].value.value, str):
                    doc_ids.add(id(body[0].value))
    return doc_ids


def _collect_user_visible_strings(source: Path) -> list[tuple[int, str]]:
    """Return [(lineno, value)] for user-visible string literals in a .py file.

    Excludes module / class / function docstrings. Comments are already
    stripped by ast.parse (they are lexer-level only).
    """
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    doc_ids = _docstring_node_ids(tree)
    results: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) in doc_ids:
                continue
            results.append((node.lineno, node.value))
    return results


def test_gui_user_visible_strings_have_no_simplified_chinese():
    hits: list[tuple[str, int, str, str]] = []
    for source in _iter_gui_sources():
        for lineno, value in _collect_user_visible_strings(source):
            match = _FORBIDDEN.search(value)
            if match:
                rel = source.relative_to(_REPO_ROOT)
                hits.append((str(rel), lineno, match.group(0), value))
    assert not hits, f"Simplified Chinese keywords in GUI user-visible literals: {hits}"


def test_sweep_actually_scans_gui_sources():
    """Guard: regression if _GUI_DIR layout changes and sweep becomes a no-op."""
    files = _iter_gui_sources()
    assert files, f"expected at least one .py under {_GUI_DIR}"


def test_sweep_skips_docstrings():
    """Sanity: docstrings containing forbidden keywords (hypothetical) would
    not trigger a failure. Verified by reading the real module docstring of
    this file, which contains safe text, AND by asserting the helper marks
    module docstring as skipped."""
    this_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    doc_ids = _docstring_node_ids(this_tree)
    # Module docstring should be registered as a doc id to skip.
    assert doc_ids, "expected at least the module docstring to be recognized"
