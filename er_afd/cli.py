"""Interfaz er-afd: retorno 1 acepta, 0 rechaza, 2 informa un error."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .automata import compile_regex
from .parser import display_char


def trace_char(char: str) -> str:
    """En el recorrido se muestra el carácter leído; solo se escapan los que confunden la línea."""
    if char in "|\\" or ord(char) <= 32 or ord(char) == 127:
        return display_char(char)
    return char


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="er-afd", description="ER -> AFND (Thompson) -> AFD (subconjuntos).",
        epilog="Retorno: 1 = aceptada, 0 = rechazada, 2 = error. Universo: ASCII 00..7F.")
    parser.add_argument("expression", metavar="ER", help="Expresión regular; use comillas para espacios.")
    parser.add_argument("text", metavar="cadena", nargs="?", help="Cadena completa; use '' para vacía.")
    parser.add_argument("--file", type=Path, metavar="RUTA", help="Leer la cadena completa de un archivo ASCII.")
    parser.add_argument("--json", action="store_true", help="Emitir autómatas y resultado como JSON.")
    parser.add_argument("--dot", type=Path, metavar="PREFIJO", help="Exportar PREFIJO.afnd.dot y PREFIJO.afd.dot.")
    parser.add_argument("--verbose", action="store_true", help="Mostrar también subconjuntos y clases del AFD.")
    parser.add_argument("--max-states", type=int, default=4096, metavar="N", help="Máximo de estados AFD (4096).")
    args = parser.parse_args(argv)
    if args.file is None and args.text is None:
        parser.error("indique una cadena o --file RUTA")
    if args.file is not None and args.text is not None:
        parser.error("use cadena o --file, pero no ambos")
    try:
        text = args.file.read_bytes().decode("ascii") if args.file else args.text
        compiled = compile_regex(args.expression, max_dfa_states=args.max_states)
        result = compiled.match(text)
        if args.dot:
            for kind, extension in (("nfa", ".afnd.dot"), ("dfa", ".afd.dot")):
                path = Path(str(args.dot) + extension)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(compiled.to_dot(kind), encoding="utf-8")
        if args.json:
            data = compiled.to_dict()
            data["input"] = text
            data["accepted"] = result.accepted
            data["exit_code"] = int(result.accepted)
            data["trace"] = [{"source": f"Q{step.source}", "symbol": step.symbol,
                              "target": f"Q{step.target}"} for step in result.trace]
            data["final_state"] = f"Q{result.final_state}"
            print(json.dumps(data, ensure_ascii=True, indent=2))
        else:
            print(compiled.format_tables(args.verbose))
            print()
            for step in result.trace:
                print(f"Q{step.source}|{trace_char(step.symbol)}|Q{step.target}")
            print("Cadena aceptada" if result.accepted else "Cadena rechazada")
        return int(result.accepted)
    except (ValueError, OSError) as error:
        if args.json:
            print(json.dumps({"error": str(error), "exit_code": 2}, ensure_ascii=True))
        else:
            print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
