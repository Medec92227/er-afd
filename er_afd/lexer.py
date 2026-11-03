"""Tokenización opcional de varias ER mediante sus matrices AFD.

Se aplica máxima longitud; a igual longitud gana la primera regla del JSON.
No se utilizan librerías de regex ni se vuelve a evaluar el parser al consumir.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys

from . import compile_regex, RegexSyntaxError, ResourceLimitError


class LexerError(ValueError):
    """Reglas inválidas, entrada no ASCII o carácter sin regla aplicable."""


@dataclass(frozen=True)
class Rule:
    name: str
    automaton: object
    skip: bool = False


@dataclass(frozen=True)
class Token:
    type: str
    value: str
    start: int
    end: int
    line: int
    column: int


def compile_rules(specification: list[dict]) -> tuple[Rule, ...]:
    """Compila reglas ordenadas, rechazando nombres repetidos y ER anulables."""
    if not isinstance(specification, list) or not specification:
        raise LexerError("Las reglas deben ser una lista JSON no vacía.")
    rules = []
    names = set()
    for index, spec in enumerate(specification, 1):
        if not isinstance(spec, dict):
            raise LexerError(f"La regla {index} debe ser un objeto JSON.")
        if set(spec) - {"name", "regex", "skip"}:
            raise LexerError(f"Campos desconocidos en regla {index}.")
        name, expression = spec.get("name"), spec.get("regex")
        skip = spec.get("skip", False)
        if not isinstance(name, str) or not name.strip() or name in names:
            raise LexerError(f"Nombre vacío, inválido o repetido en regla {index}.")
        if not isinstance(expression, str) or type(skip) is not bool:
            raise LexerError(f"regex debe ser texto y skip booleano en regla {index}.")
        compiled = compile_regex(expression)
        if compiled.accepts(""):
            raise LexerError(f"La regla {name} acepta vacío; impediría avanzar.")
        names.add(name)
        rules.append(Rule(name, compiled, skip))
    return tuple(rules)


def tokenize(rules: tuple[Rule, ...], text: str) -> list[Token]:
    """Devuelve todos los tokens o falla; posiciones base 0, línea/columna base 1.

    Los offsets end son exclusivos. Un LF incrementa la línea; CR se cuenta
    como carácter ordinario. El archivo se lee en bytes para preservar CR/LF.
    """
    if not rules:
        raise LexerError("Se necesita al menos una regla.")
    if any(ord(char) > 127 for char in text):
        raise LexerError("El texto de entrada debe estar en ASCII (0..127).")
    tokens = []
    position, line, column = 0, 1, 1
    while position < len(text):
        active = [(index, rule.automaton.dfa.start)
                  for index, rule in enumerate(rules)]
        best_rule, best_end = None, position
        cursor = position
        while active and cursor < len(text):
            following = []
            winners = []
            for index, state in active:
                dfa = rules[index].automaton.dfa
                target = dfa.step(state, text[cursor])
                if target is None or target == dfa.dead_state:
                    continue
                following.append((index, target))
                if target in dfa.finals:
                    winners.append(index)
            cursor += 1
            if winners:
                best_rule, best_end = min(winners), cursor
            active = following
        if best_rule is None:
            raise LexerError(
                f"Sin regla para {text[position]!r} en línea {line}, "
                f"columna {column}, offset {position}."
            )
        value = text[position:best_end]
        rule = rules[best_rule]
        if not rule.skip:
            tokens.append(Token(rule.name, value, position, best_end, line, column))
        for char in value:
            if char == "\n":
                line, column = line + 1, 1
            else:
                column += 1
        position = best_end
    return tokens


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="er-lex", description="Tokeniza ASCII usando varias ER y matrices AFD."
    )
    parser.add_argument("--rules", required=True, type=Path, help="Reglas JSON ordenadas")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", type=Path, help="Archivo ASCII; conserva saltos de línea")
    source.add_argument("--text", help="Texto ASCII entre comillas")
    args = parser.parse_args(argv)
    try:
        spec = json.loads(args.rules.read_text(encoding="utf-8-sig"))
        rules = compile_rules(spec)
        text = args.file.read_bytes().decode("ascii") if args.file else args.text
        result = tokenize(rules, text)
        print(json.dumps([asdict(token) for token in result], ensure_ascii=True, indent=2))
        return 0
    except (OSError, ValueError, RegexSyntaxError, ResourceLimitError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
