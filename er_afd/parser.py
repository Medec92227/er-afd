"""Analizador descendente recursivo de las ER del enunciado.

No utiliza motores de expresiones regulares. El universo de entrada es ASCII
(0..127); el carácter épsilon se reserva para la cadena vacía en la ER.
"""
from __future__ import annotations

from dataclasses import dataclass

EPSILON = "ε"
ASCII = frozenset(chr(i) for i in range(128))
MAX_PATTERN_LENGTH = 4096
MAX_NESTING = 100


class RegexSyntaxError(ValueError):
    """Expresión mal formada, con posición de origen (basada en uno)."""

    def __init__(self, message: str, position: int):
        self.position = position
        super().__init__(f"{message} (posición {position + 1})")


class ResourceLimitError(ValueError):
    """La ER o el autómata superan el tamaño máximo permitido."""


def display_char(char: str) -> str:
    """Cómo se muestra un carácter en las tablas (espacios y controles en hexadecimal)."""
    if char == " ":
        return r"\h20"
    if ord(char) < 32 or ord(char) == 127:
        return "\\h" + f"{ord(char):02X}"
    if char in "\\.|*()[]{}^,-":
        return "\\" + char
    return char


@dataclass(frozen=True)
class Node:
    kind: str
    children: tuple["Node", ...] = ()
    # Cada símbolo es (etiqueta que se muestra, caracteres ASCII que representa).
    symbols: tuple[tuple[str, frozenset[str]], ...] = ()


@dataclass(frozen=True)
class ParsedRegex:
    tree: Node
    alphabet: tuple[str, ...]
    symbol_sets: dict[str, frozenset[str]]


class Parser:
    def __init__(self, pattern: str):
        if not isinstance(pattern, str):
            raise TypeError("La expresión regular debe ser texto.")
        if len(pattern) > MAX_PATTERN_LENGTH:
            raise ResourceLimitError(f"La ER supera {MAX_PATTERN_LENGTH} caracteres.")
        self.pattern = pattern
        self.pos = 0
        self.depth = 0
        self.alphabet: list[str] = []
        self.symbol_sets: dict[str, frozenset[str]] = {}

    def error(self, message: str, pos: int | None = None) -> RegexSyntaxError:
        return RegexSyntaxError(message, self.pos if pos is None else pos)

    def peek(self) -> str:
        return self.pattern[self.pos] if self.pos < len(self.pattern) else ""

    def register(self, label: str, chars: frozenset[str]) -> None:
        if label not in self.alphabet:
            self.alphabet.append(label)
            self.symbol_sets[label] = chars

    def literal(self, char: str, position: int) -> tuple[str, frozenset[str]]:
        if char not in ASCII:
            raise self.error("El literal debe pertenecer a ASCII (00..7F)", position)
        return display_char(char), frozenset((char,))

    def parse(self) -> ParsedRegex:
        if not self.pattern:
            raise self.error("La ER está vacía; use ε para la cadena vacía")
        tree = self.union()
        if self.peek():
            raise self.error(f"Símbolo inesperado {self.peek()!r}")
        return ParsedRegex(tree, tuple(self.alphabet), dict(self.symbol_sets))

    def union(self) -> Node:
        children = [self.concat()]
        while self.peek() == "|":
            self.pos += 1
            children.append(self.concat())
        return children[0] if len(children) == 1 else Node("union", tuple(children))

    def concat(self) -> Node:
        children: list[Node] = []
        while self.peek() and self.peek() not in "|)":
            children.append(self.repeat())
        if not children:
            raise self.error("Falta un operando; use ε para una rama vacía")
        return children[0] if len(children) == 1 else Node("concat", tuple(children))

    def repeat(self) -> Node:
        node = self.atom()
        while self.peek() == "*":
            self.pos += 1
            node = Node("star", (node,))
        return node

    def atom(self) -> Node:
        start = self.pos
        char = self.peek()
        if char == "(":
            self.pos += 1
            self.depth += 1
            if self.depth > MAX_NESTING:
                raise ResourceLimitError(f"Se exceden {MAX_NESTING} niveles de paréntesis.")
            node = self.union()
            if self.peek() != ")":
                raise self.error("Falta cerrar el paréntesis", start)
            self.pos += 1
            self.depth -= 1
            return node
        if char == "*":
            raise self.error("La cerradura * necesita un operando")
        if char == "]":
            raise self.error("Corchete de cierre sin conjunto")
        if char == EPSILON:
            self.pos += 1
            self.register(EPSILON, frozenset())
            return Node("epsilon")
        if char == ".":
            self.pos += 1
            symbols = ((".", ASCII),)
        elif char == "[":
            symbols = self.character_class()
        elif char == "\\":
            symbols = self.escape()
        else:
            self.pos += 1
            symbols = (self.literal(char, start),)
        for label, chars in symbols:
            self.register(label, chars)
        return Node("symbols", symbols=tuple(symbols))

    def escape(self) -> tuple[tuple[str, frozenset[str]], ...]:
        start = self.pos
        self.pos += 1
        if not self.peek():
            raise self.error("Secuencia de escape incompleta", start)
        char = self.peek()
        self.pos += 1
        macros = {"N": "0123456789", "A": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                  "a": "abcdefghijklmnopqrstuvwxyz",
                  "z": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"}
        if char in macros:
            return tuple(self.literal(c, start) for c in macros[char])
        if char == "h":
            digits = self.pattern[self.pos:self.pos + 2]
            if len(digits) != 2 or any(c not in "0123456789abcdefABCDEF" for c in digits):
                raise self.error("\\h exige exactamente dos dígitos hexadecimales", start)
            value = int(digits, 16)
            if value > 127:
                raise self.error("El código hexadecimal debe estar entre 00 y 7F", start)
            self.pos += 2
            return (self.literal(chr(value), start),)
        return (self.literal(char, start),)

    def class_unit(self) -> tuple[tuple[str, frozenset[str]], ...]:
        start = self.pos
        if self.peek() == "\\":
            return self.escape()
        char = self.peek()
        if not char or char == "]":
            raise self.error("Falta un carácter en el conjunto")
        self.pos += 1
        return (self.literal(char, start),)

    def character_class(self) -> tuple[tuple[str, frozenset[str]], ...]:
        start = self.pos
        self.pos += 1
        negate = self.peek() == "^"
        if negate:
            self.pos += 1
        symbols: list[tuple[str, frozenset[str]]] = []
        while self.peek() and self.peek() != "]":
            unit_start = self.pos
            left = self.class_unit()
            # El guion es literal si va al inicio o al final del conjunto.
            if self.peek() == "-" and self.pos + 1 < len(self.pattern) and self.pattern[self.pos + 1] != "]":
                self.pos += 1
                right = self.class_unit()
                if len(left) != 1 or len(right) != 1:
                    raise self.error("Los extremos del rango deben ser caracteres individuales", unit_start)
                lo = ord(next(iter(left[0][1])))
                hi = ord(next(iter(right[0][1])))
                if lo > hi:
                    raise self.error("Rango invertido en el conjunto", unit_start)
                symbols.extend(self.literal(chr(i), unit_start) for i in range(lo, hi + 1))
            else:
                symbols.extend(left)
        if self.peek() != "]":
            raise self.error("Falta cerrar el conjunto ]", start)
        self.pos += 1
        if not symbols:
            raise self.error("El conjunto no puede estar vacío", start)
        unique = dict(symbols)
        if negate:
            excluded = frozenset(c for chars in unique.values() for c in chars)
            label = "[^" + "".join(unique) + "]"
            return ((label, ASCII - excluded),)
        return tuple(unique.items())


def parse_regex(pattern: str) -> ParsedRegex:
    """Analiza y valida sin evaluar mediante bibliotecas de regex."""
    return Parser(pattern).parse()
