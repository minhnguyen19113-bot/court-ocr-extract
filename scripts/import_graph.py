from __future__ import annotations

import argparse
import ast
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ["src", "scripts", "tests"]
PACKAGE_PREFIX = "court_ocr_extract"
ENTRYPOINT_MODULES = {
    "court_ocr_extract.cli",
    "scripts.run_batch",
    "scripts.run_single",
    "scripts.transfer_server",
}


@dataclass(frozen=True)
class ImportGraph:
    modules: dict[str, str]
    imports: dict[str, list[str]]
    reverse_imports: dict[str, list[str]]
    internal_imports: dict[str, list[str]]
    unimported_src_modules: list[str]
    parse_errors: dict[str, str]


def iter_python_files(repo_root: Path = REPO_ROOT) -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        folder = repo_root / root
        if not folder.exists():
            continue
        for path in folder.rglob("*.py"):
            if "__pycache__" not in path.parts:
                files.append(path)
    return sorted(files)


def module_name_for_path(path: Path, repo_root: Path = REPO_ROOT) -> str:
    relative = path.relative_to(repo_root)
    parts = list(relative.with_suffix("").parts)
    if parts[0] == "src":
        parts = parts[1:]
    return ".".join(parts)


def imported_modules_from_ast(tree: ast.AST, module: str) -> list[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            base = _resolve_import_from(node, module)
            if base:
                imports.add(base)
            for alias in node.names:
                if alias.name == "*":
                    continue
                if base:
                    imports.add(f"{base}.{alias.name}")
    return sorted(imports)


def _resolve_import_from(node: ast.ImportFrom, module: str) -> str:
    if node.level <= 0:
        return node.module or ""
    package_parts = module.split(".")[:-1]
    keep = max(len(package_parts) - node.level + 1, 0)
    prefix = package_parts[:keep]
    if node.module:
        prefix.extend(node.module.split("."))
    return ".".join(prefix)


def _canonical_internal(import_name: str, modules: set[str]) -> str | None:
    if import_name in modules:
        return import_name
    parts = import_name.split(".")
    while len(parts) > 1:
        parts.pop()
        candidate = ".".join(parts)
        if candidate in modules:
            return candidate
    return None


def build_import_graph(repo_root: Path = REPO_ROOT) -> ImportGraph:
    modules = {
        module_name_for_path(path, repo_root): path.relative_to(repo_root).as_posix()
        for path in iter_python_files(repo_root)
    }
    module_names = set(modules)
    imports: dict[str, list[str]] = {}
    parse_errors: dict[str, str] = {}

    for module, relative_path in modules.items():
        path = repo_root / relative_path
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative_path)
        except SyntaxError as exc:
            parse_errors[relative_path] = str(exc)
            imports[module] = []
            continue
        imports[module] = imported_modules_from_ast(tree, module)

    reverse: dict[str, set[str]] = defaultdict(set)
    internal_imports: dict[str, set[str]] = defaultdict(set)
    for module, imported_names in imports.items():
        for imported_name in imported_names:
            internal = _canonical_internal(imported_name, module_names)
            if internal is None:
                continue
            reverse[internal].add(module)
            internal_imports[module].add(internal)

    unimported = []
    for module in module_names:
        if not module.startswith(f"{PACKAGE_PREFIX}."):
            continue
        if module.endswith(".__init__") or module in ENTRYPOINT_MODULES:
            continue
        if module not in reverse:
            unimported.append(module)

    return ImportGraph(
        modules=dict(sorted(modules.items())),
        imports={key: sorted(value) for key, value in sorted(imports.items())},
        reverse_imports={key: sorted(value) for key, value in sorted(reverse.items())},
        internal_imports={key: sorted(value) for key, value in sorted(internal_imports.items())},
        unimported_src_modules=sorted(unimported),
        parse_errors=dict(sorted(parse_errors.items())),
    )


def graph_to_dict(graph: ImportGraph) -> dict[str, Any]:
    return asdict(graph)


def format_import_graph(graph: ImportGraph) -> str:
    lines = [
        "Import graph: PASS" if not graph.parse_errors else "Import graph: WARN",
        f"Python modules scanned: {len(graph.modules)}",
        f"Internal import edges: {sum(len(v) for v in graph.internal_imports.values())}",
        f"Unimported src modules: {len(graph.unimported_src_modules)}",
    ]
    if graph.parse_errors:
        lines.extend(["", "Parse errors:"])
        for path, error in graph.parse_errors.items():
            lines.append(f"- {path}: {error}")
    lines.extend(["", "Duplicate/low-fan-in candidates from graph:"])
    for module in graph.unimported_src_modules[:30]:
        lines.append(f"- {module}")
    if len(graph.unimported_src_modules) > 30:
        lines.append(f"- ... {len(graph.unimported_src_modules) - 30} more")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a safe Python import graph.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    graph = build_import_graph()
    if args.json:
        print(json.dumps(graph_to_dict(graph), ensure_ascii=False, indent=2))
    else:
        print(format_import_graph(graph))
    return 0 if not graph.parse_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
