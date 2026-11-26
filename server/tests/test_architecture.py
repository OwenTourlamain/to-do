"""Layering rules, enforced: storage details must not leak out of the db package."""

import ast
from pathlib import Path

import todo_server

PACKAGE_DIR = Path(todo_server.__file__).parent
STORAGE_LIBRARIES = {"sqlalchemy", "alembic"}


def _imported_roots(path: Path) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def _imported_modules(path: Path) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _source_files_outside(subpackage: str) -> list[Path]:
    inside = PACKAGE_DIR / subpackage
    return [p for p in PACKAGE_DIR.rglob("*.py") if inside not in p.parents]


def test_only_db_imports_storage_libraries() -> None:
    offenders = {
        str(path.relative_to(PACKAGE_DIR)): sorted(_imported_roots(path) & STORAGE_LIBRARIES)
        for path in _source_files_outside("db")
        if _imported_roots(path) & STORAGE_LIBRARIES
    }
    assert offenders == {}


def test_only_db_facade_is_imported_from_outside() -> None:
    offenders = {
        str(path.relative_to(PACKAGE_DIR)): sorted(
            m for m in _imported_modules(path) if m.startswith("todo_server.db.")
        )
        for path in _source_files_outside("db")
    }
    assert {k: v for k, v in offenders.items() if v} == {}


def test_models_depend_on_nothing_else_in_the_app() -> None:
    for path in (PACKAGE_DIR / "models").rglob("*.py"):
        internal = {m for m in _imported_modules(path) if m.startswith("todo_server.")}
        assert internal <= {
            "todo_server.models",
            "todo_server.models.enums",
            "todo_server.models.entities",
        }, path
