"""Shared helpers for the DDD domain-migration test suites (#9, #10, #12, ...).

Each domain-migration test module (test_core_domain_migration.py,
test_export_domain_migration.py, test_generation_domain_migration.py, and
whichever future phase's test follows) needs to AST-scan a domain's files for
imports it isn't allowed to make. Centralized here so a fix (e.g. handling
relative imports or TYPE_CHECKING blocks) only needs to happen once.
"""

import ast
from pathlib import Path


def imported_modules(file_path: Path) -> list[str]:
    """Return the dotted module names a Python file imports."""
    tree = ast.parse(
        file_path.read_text(encoding="utf-8"), filename=str(file_path)
    )
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules
