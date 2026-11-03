#!/usr/bin/env python3
"""Pasos del Makefile: config, build, run, web y clean. Solo usa la biblioteca estándar."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipapp


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "er_afd"
BUILD = ROOT / "build"
DIST = ROOT / "dist"
ENTRY_POINTS = {"er-afd": "cli", "er-lex": "lexer"}


def config() -> int:
    if sys.version_info < (3, 10):
        print("Error: se requiere Python 3.10 o posterior.", file=sys.stderr)
        return 2
    print(f"Python {sys.version.split()[0]}: OK")
    print("No hay dependencias externas que instalar.")
    return 0


def build() -> int:
    if config():
        return 2
    # Detecta errores de sintaxis antes de empaquetar.
    for source in PACKAGE.rglob("*.py"):
        compile(source.read_text(encoding="utf-8"), str(source), "exec")
    DIST.mkdir(exist_ok=True)
    for name, module in ENTRY_POINTS.items():
        stage = BUILD / name
        shutil.rmtree(stage, ignore_errors=True)
        stage.mkdir(parents=True)
        shutil.copytree(PACKAGE, stage / "er_afd", ignore=shutil.ignore_patterns("__pycache__"))
        (stage / "__main__.py").write_text(
            f"from er_afd.{module} import main\nraise SystemExit(main())\n", encoding="utf-8")
        target = DIST / name
        zipapp.create_archive(stage, target=target, interpreter="/usr/bin/env python3", compressed=True)
        target.chmod(0o755)
        print(f"Construido: dist/{name}")
    shutil.rmtree(BUILD, ignore_errors=True)
    return 0


def run() -> int:
    target = DIST / "er-afd"
    if not target.is_file() and build():
        return 2
    pattern = os.environ.get("ER", "(a|b)*abb")
    text = os.environ.get("CADENA", "aabb")
    code = subprocess.run([sys.executable, str(target), pattern, text], cwd=ROOT).returncode
    # 1 y 0 son respuestas válidas del programa (aceptada / rechazada), no fallos de make.
    if code in (0, 1):
        print(f"Código de retorno: {code}")
        return 0
    return code


def web() -> int:
    """Arma dist/web: la página de web/ más el paquete er_afd que ejecuta Pyodide."""
    target = DIST / "web"
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(ROOT / "web", target)
    shutil.copytree(PACKAGE, target / "er_afd", ignore=shutil.ignore_patterns("__pycache__"))
    print("Página lista en dist/web")
    print("Para verla: python3 -m http.server 8000 -d dist/web  y abrir http://localhost:8000")
    return 0


def clean() -> int:
    shutil.rmtree(BUILD, ignore_errors=True)
    shutil.rmtree(DIST, ignore_errors=True)
    for cache in ROOT.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    print("Se eliminaron build/, dist/ y __pycache__.")
    return 0


def main() -> int:
    commands = {"config": config, "build": build, "run": run, "web": web, "clean": clean}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        print("Uso: python3 tools/build.py {config|build|run|web|clean}", file=sys.stderr)
        return 2
    return commands[sys.argv[1]]()


if __name__ == "__main__":
    raise SystemExit(main())
