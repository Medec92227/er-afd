#!/usr/bin/env python3
"""Configuración, zipapps y ejecución reproducibles con biblioteca estándar."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipapp


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "er_afd"
ENTRY_POINTS = {"er-afd": "cli", "er-lex": "lexer"}


def config() -> int:
    if sys.version_info < (3, 10):
        print("Error: se requiere Python 3.10 o posterior.", file=sys.stderr)
        return 2
    print(f"Python {sys.version.split()[0]}: configuración válida.")
    print("Ejecución sin paquetes externos, sin red y sin privilegios root.")
    return 0


def safe_remove(path: Path, parent: Path) -> None:
    """Borra únicamente un hijo real del directorio de trabajo esperado."""
    resolved = path.resolve()
    expected = parent.resolve()
    workspace = ROOT.resolve()
    if expected == workspace or workspace not in expected.parents:
        raise ValueError(f"Directorio de limpieza fuera del proyecto: {parent}")
    if resolved == expected or expected not in resolved.parents:
        raise ValueError(f"Ruta de limpieza fuera del destino permitido: {path}")
    if path.is_symlink():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def build() -> int:
    if config():
        return 2
    if not (PACKAGE / "__init__.py").is_file():
        print("Error: no se encuentra el paquete er_afd.", file=sys.stderr)
        return 2
    for source in PACKAGE.rglob("*.py"):
        compile(source.read_text(encoding="utf-8"), str(source), "exec")
    (ROOT / "dist").mkdir(exist_ok=True)
    for name, module in ENTRY_POINTS.items():
        stage = ROOT / "build" / ("zipapp_" + name)
        if stage.exists():
            safe_remove(stage, ROOT / "build")
        stage.mkdir(parents=True)
        shutil.copytree(PACKAGE, stage / "er_afd", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (stage / "__main__.py").write_text(
            f"from er_afd.{module} import main\nraise SystemExit(main())\n",
            encoding="utf-8",
        )
        target = ROOT / "dist" / name
        zipapp.create_archive(stage, target=target, interpreter="/usr/bin/env python3", compressed=True)
        target.chmod(0o755)
        safe_remove(stage, ROOT / "build")
        print(f"Construido: dist/{name}")
    return 0


def run() -> int:
    target = ROOT / "dist" / "er-afd"
    if not target.is_file() and build():
        return 2
    pattern = os.environ.get("ER", "(a|b)*abb")
    text = os.environ.get("CADENA", "aabb")
    result = subprocess.run([sys.executable, str(target), pattern, text], cwd=ROOT, check=False)
    if result.returncode in (0, 1):
        label = "aceptada" if result.returncode == 1 else "rechazada"
        print(f"[make run] Código del programa: {result.returncode} ({label}).")
        return 0
    return result.returncode


def clean() -> int:
    for name in ENTRY_POINTS:
        safe_remove(ROOT / "dist" / name, ROOT / "dist")
        safe_remove(ROOT / "build" / ("zipapp_" + name), ROOT / "build")
    for base in (PACKAGE, ROOT / "tests", ROOT / "tools"):
        if base.is_dir():
            for cache in sorted(base.rglob("__pycache__"), key=lambda p: len(p.parts), reverse=True):
                safe_remove(cache, base)
    print("Limpieza completada: zipapps, staging y cachés Python.")
    print("Se conservan código, documentación, ejemplos y evidencias.")
    return 0


def main() -> int:
    commands = {"config": config, "build": build, "run": run, "clean": clean}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        print("Uso: python3 tools/build.py {config|build|run|clean}", file=sys.stderr)
        return 2
    try:
        return commands[sys.argv[1]]()
    except (OSError, ValueError, SyntaxError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
