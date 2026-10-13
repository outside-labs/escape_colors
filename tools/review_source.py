"""Review Python syntax and runtime imports without executing project code."""

import argparse
import ast
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys
import tokenize
import warnings


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    column: int
    code: str
    message: str


def source_files(root: Path) -> list[Path]:
    files = []
    for directory in ("src", "tests", "examples", "tools"):
        for path in (root / directory).rglob("*.py"):
            if path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root):
                files.append(path)
    return sorted(files)


def module_name(path: Path, source: Path) -> tuple[str, ...]:
    relative = path.relative_to(source)
    parts = (*relative.parts[:-1], relative.stem)
    return parts[:-1] if relative.name == "__init__.py" else parts


def import_findings(
    tree: ast.Module,
    path: str,
    module: tuple[str, ...],
    is_package: bool,
    modules: set[tuple[str, ...]],
    lines: list[str],
) -> list[Finding]:
    findings = []
    local_roots = {name[0] for name in modules if name}
    standard = sys.stdlib_module_names | set(sys.builtin_module_names)
    package = module if is_package else module[:-1]

    def finding(node: ast.AST, code: str, message: str) -> Finding:
        prefix = lines[node.lineno - 1].encode("utf-8")[:node.col_offset]
        column = len(prefix.decode("utf-8")) + 1
        return Finding(path, node.lineno, column, code, message)

    def check_absolute(name: str, node: ast.AST) -> None:
        parts = tuple(name.split("."))
        if parts[0] in local_roots:
            if parts not in modules:
                findings.append(finding(node, "MISSING_MODULE", f"local module '{name}' does not exist"))
        elif parts[0] not in standard:
            findings.append(finding(node, "NON_STDLIB_IMPORT",
                                    f"runtime import '{name}' is outside the standard library and local modules"))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                check_absolute(alias.name, alias)
        elif isinstance(node, ast.ImportFrom):
            if not node.level:
                check_absolute(node.module, node)
            elif node.level > len(package):
                findings.append(finding(node, "MISSING_MODULE", "relative import goes beyond the local package"))
            else:
                base = package[:len(package) - node.level + 1]
                target = (*base, *node.module.split(".")) if node.module else base
                if target not in modules:
                    findings.append(finding(node, "MISSING_MODULE", f"local module '{'.'.join(target)}' does not exist"))
    return findings


def review(root: Path) -> tuple[int, list[Finding]]:
    source = root / "src"
    files = source_files(root)
    modules = set()
    for path in files:
        if path.is_relative_to(source):
            name = module_name(path, source)
            modules.update(name[:length] for length in range(1, len(name) + 1))
    findings = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        try:
            with tokenize.open(path) as file:
                text = file.read()
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always", SyntaxWarning)
                tree = ast.parse(text, filename=str(path))
                compile(tree, str(path), "exec", dont_inherit=True)
            for warning in captured:
                if issubclass(warning.category, SyntaxWarning):
                    findings.append(Finding(relative, warning.lineno, 1,
                                            "SYNTAX_WARNING", str(warning.message)))
        except SyntaxError as error:
            findings.append(Finding(relative, error.lineno or 1, error.offset or 1,
                                    "SYNTAX", error.msg))
            continue
        except (OSError, UnicodeError) as error:
            findings.append(Finding(relative, 1, 1, "READ_ERROR", str(error)))
            continue
        if path.is_relative_to(source):
            findings.extend(import_findings(tree, relative, module_name(path, source),
                                            path.name == "__init__.py", modules, text.splitlines()))
    return len(files), sorted(findings, key=lambda finding: (finding.path, finding.line, finding.column, finding.code))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root / "src").is_dir():
        parser.error("root must contain a src directory")
    checked, findings = review(root)
    if args.format == "json":
        print(json.dumps({"checked": checked, "findings": [asdict(finding) for finding in findings]}, indent=2))
    else:
        for finding in findings:
            print(f"{finding.path}:{finding.line}:{finding.column}: {finding.code}: {finding.message}")
        print(f"Reviewed {checked} Python files; findings: {len(findings)}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
