"""Verify the wheel and source archive in isolated, clean installations."""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib


ROOT = Path(__file__).resolve().parents[1]
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


def run(*args: str, cwd: Path) -> None:
    subprocess.run(args, check=True, cwd=cwd)


def verify_wheel(wheel: Path, work: Path) -> None:
    work.mkdir()
    environment = work / "environment"
    run(sys.executable, "-m", "venv", "--without-pip", str(environment), cwd=work)
    python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    run("uv", "pip", "install", "--python", str(python), "--no-index", "--no-deps", str(wheel), cwd=work)
    shutil.copytree(ROOT / "tests", work / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "tools", work / "tools", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(ROOT / "README.md", work / "README.md")
    run(str(python), "-I", str(work / "tools/review_source.py"), "--root", str(ROOT), cwd=work)
    run(str(python), "-I", "-c", """
import importlib.metadata
from pathlib import Path
import sys
import escape_colors
assert 'site-packages' in Path(escape_colors.__file__).parts, escape_colors.__file__
assert importlib.metadata.version('escape-colors') == sys.argv[1]
assert not importlib.metadata.requires('escape-colors')
""", VERSION, cwd=work)
    run(str(python), "-I", "-m", "unittest", "discover", "-s", str(work / "tests"), "-q", cwd=work)
    subprocess.run([str(python), "-I", "-X", "utf8", str(ROOT / "examples/basic.py")], cwd=work,
                   check=True, capture_output=True, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    dist = args.dist.resolve()
    wheels = list(dist.glob("escape_colors-*.whl"))
    archives = list(dist.glob("escape_colors-*.tar.gz"))
    if len(wheels) != 1 or len(archives) != 1:
        parser.error("expected one wheel and one source archive; run uv build first")
    with tempfile.TemporaryDirectory(prefix="escape-colors-check-") as temporary:
        work = Path(temporary)
        verify_wheel(wheels[0], work / "wheel")
        with tarfile.open(archives[0]) as archive:
            archive.extractall(work / "source", filter="data")
        sources = list((work / "source").iterdir())
        if len(sources) != 1 or not (sources[0] / "pyproject.toml").is_file():
            raise ValueError("source archive does not contain one complete project")
        rebuilt = work / "rebuilt"
        run("uv", "build", "--wheel", "--out-dir", str(rebuilt), str(sources[0]), cwd=work)
        rebuilt_wheels = list(rebuilt.glob("*.whl"))
        if len(rebuilt_wheels) != 1:
            raise ValueError("source build did not produce one wheel")
        verify_wheel(rebuilt_wheels[0], work / "source-wheel")
    print("Verified wheel and source archive in clean installations.")


if __name__ == "__main__":
    main()
