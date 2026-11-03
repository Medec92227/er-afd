"""Construcción explícita de Thompson, subconjuntos y simulación tabular."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .parser import (ASCII, EPSILON, Node, ParsedRegex, ResourceLimitError,
                     display_char, parse_regex)


@dataclass(frozen=True)
class Step:
    source: int
    symbol: str
    target: int


@dataclass(frozen=True)
class MatchResult:
    accepted: bool
    trace: tuple[Step, ...]
    final_state: int


@dataclass
class NFA:
    state_count: int
    start: int
    finals: frozenset[int]
    alphabet: tuple[str, ...]
    symbol_sets: dict[str, frozenset[str]]
    transitions: dict[tuple[int, str], frozenset[int]]

    def epsilon_closure(self, states: set[int] | frozenset[int]) -> frozenset[int]:
        seen = set(states)
        pending = list(states)
        while pending:
            state = pending.pop()
            for target in self.transitions.get((state, EPSILON), ()):
                if target not in seen:
                    seen.add(target)
                    pending.append(target)
        return frozenset(seen)

    def move(self, states: frozenset[int], char: str) -> frozenset[int]:
        targets: set[int] = set()
        for state in states:
            for label in self.alphabet:
                if label != EPSILON and char in self.symbol_sets[label]:
                    targets.update(self.transitions.get((state, label), ()))
        return frozenset(targets)

    def accepts(self, text: str) -> bool:
        validate_ascii(text)
        states = self.epsilon_closure(frozenset((self.start,)))
        for char in text:
            states = self.epsilon_closure(self.move(states, char))
        return bool(states & self.finals)


@dataclass
class DFA:
    start: int
    finals: frozenset[int]
    alphabet: tuple[str, ...]
    source_alphabet: tuple[str, ...]
    symbol_sets: dict[str, frozenset[str]]
    transitions: dict[tuple[int, str], int]
    subsets: tuple[frozenset[int], ...]
    char_classes: dict[str, str]
    dead_state: int | None

    @property
    def state_count(self) -> int:
        return len(self.subsets)

    def step(self, state: int, char: str) -> int:
        if len(char) != 1 or char not in ASCII:
            raise ValueError("La transición requiere un carácter ASCII.")
        return self.transitions[(state, self.char_classes[char])]

    def match(self, text: str) -> MatchResult:
        validate_ascii(text)
        state = self.start
        trace = []
        for char in text:
            target = self.step(state, char)
            trace.append(Step(state, char, target))
            state = target
        return MatchResult(state in self.finals, tuple(trace), state)

    def accepts(self, text: str) -> bool:
        validate_ascii(text)
        state = self.start
        for char in text:
            state = self.step(state, char)
        return state in self.finals


def validate_ascii(text: str) -> None:
    if not isinstance(text, str):
        raise TypeError("La cadena debe ser texto.")
    for i, char in enumerate(text):
        if char not in ASCII:
            raise ValueError(f"La cadena contiene un carácter no ASCII en posición {i + 1}.")


def thompson(parsed: ParsedRegex) -> NFA:
    """Compila el AST por postorden, sin recursión sobre concatenaciones largas."""
    next_state = 0
    edges: dict[tuple[int, str], set[int]] = {}

    def state() -> int:
        nonlocal next_state
        value = next_state
        next_state += 1
        if next_state > 20000:
            raise ResourceLimitError("El AFND supera 20000 estados.")
        return value

    def edge(source: int, label: str, target: int) -> None:
        edges.setdefault((source, label), set()).add(target)

    pending: list[tuple[Node, bool]] = [(parsed.tree, False)]
    fragments: list[tuple[int, int]] = []
    while pending:
        node, ready = pending.pop()
        if not ready:
            pending.append((node, True))
            pending.extend((child, False) for child in reversed(node.children))
            continue
        if node.kind in ("symbols", "epsilon"):
            start, end = state(), state()
            if node.kind == "epsilon":
                edge(start, EPSILON, end)
            for label, _ in node.symbols:
                edge(start, label, end)
        else:
            count = len(node.children)
            children = fragments[-count:]
            del fragments[-count:]
            if node.kind == "concat":
                start, end = children[0][0], children[-1][1]
                for (_, previous), (following, _) in zip(children, children[1:]):
                    edge(previous, EPSILON, following)
            elif node.kind == "union":
                start, end = state(), state()
                for child_start, child_end in children:
                    edge(start, EPSILON, child_start)
                    edge(child_end, EPSILON, end)
            elif node.kind == "star":
                start, end = state(), state()
                child_start, child_end = children[0]
                edge(start, EPSILON, child_start)
                edge(start, EPSILON, end)
                edge(child_end, EPSILON, child_start)
                edge(child_end, EPSILON, end)
            else:
                raise AssertionError(f"Tipo de nodo desconocido: {node.kind}")
        fragments.append((start, end))
    initial, final = fragments[0]
    # Thompson creates union/star wrappers last; renumber to guarantee q0.
    old_order = [initial] + [s for s in range(next_state) if s != initial]
    mapping = {old: new for new, old in enumerate(old_order)}
    renamed = {(mapping[s], label): frozenset(mapping[t] for t in targets)
               for (s, label), targets in edges.items()}
    alphabet = parsed.alphabet
    if EPSILON not in alphabet:
        alphabet += (EPSILON,)
    symbols = dict(parsed.symbol_sets)
    symbols[EPSILON] = frozenset()
    return NFA(next_state, 0, frozenset((mapping[final],)), alphabet, symbols, renamed)


def _partitions(nfa: NFA) -> tuple[dict[str, frozenset[str]], dict[str, str]]:
    """Agrupa caracteres con idéntica pertenencia a las etiquetas del AFND.

    Evita la falsa determinación de una tabla con columnas solapadas a y . .
    Incluye la clase residual para tener una función total sobre ASCII.
    """
    labels = tuple(label for label in nfa.alphabet if label != EPSILON)
    groups: dict[tuple[str, ...], list[str]] = {}
    order = []
    # Preserve the first appearance of concrete source symbols, then residual.
    for label in labels:
        order.extend(sorted(nfa.symbol_sets[label], key=ord))
    order.extend(chr(i) for i in range(128))
    for char in dict.fromkeys(order):
        signature = tuple(label for label in labels if char in nfa.symbol_sets[label])
        groups.setdefault(signature, []).append(char)
    symbol_sets: dict[str, frozenset[str]] = {}
    char_classes = {}
    for i, (signature, chars) in enumerate(groups.items()):
        group = frozenset(chars)
        if len(group) == 1:
            label = display_char(chars[0])
        elif len(signature) == 1 and group == nfa.symbol_sets[signature[0]]:
            label = signature[0]
        else:
            label = f"C{i}"
        # Source literal C0 is displayed one character at a time, no collision.
        if label in symbol_sets:
            label = f"C{i}"
        symbol_sets[label] = group
        char_classes.update((char, label) for char in group)
    return symbol_sets, char_classes


def determinize(nfa: NFA, max_states: int = 4096) -> DFA:
    if max_states < 1:
        raise ValueError("El máximo de estados del AFD debe ser positivo.")
    symbols, char_classes = _partitions(nfa)
    start_subset = nfa.epsilon_closure(frozenset((nfa.start,)))
    subsets = [start_subset]
    indices = {start_subset: 0}
    pending = deque((start_subset,))
    transitions: dict[tuple[int, str], int] = {}
    finals: set[int] = set()
    # Cache each individual state's consuming move per partition.
    moves: dict[tuple[int, str], frozenset[int]] = {}
    outgoing: dict[int, list[tuple[frozenset[str], frozenset[int]]]] = {}
    for (source, label), targets in nfa.transitions.items():
        if label != EPSILON:
            outgoing.setdefault(source, []).append((nfa.symbol_sets[label], targets))
    for state in range(nfa.state_count):
        for partition, chars in symbols.items():
            representative = min(chars, key=ord)
            targets: set[int] = set()
            for character_set, destinations in outgoing.get(state, ()):
                if representative in character_set:
                    targets.update(destinations)
            moves[(state, partition)] = frozenset(targets)
    while pending:
        subset = pending.popleft()
        source = indices[subset]
        if subset & nfa.finals:
            finals.add(source)
        for label in symbols:
            targets: set[int] = set()
            for state in subset:
                targets.update(moves[(state, label)])
            target_subset = nfa.epsilon_closure(frozenset(targets))
            if target_subset not in indices:
                if len(subsets) >= max_states:
                    raise ResourceLimitError(f"El AFD supera el límite de {max_states} estados.")
                indices[target_subset] = len(subsets)
                subsets.append(target_subset)
                pending.append(target_subset)
            transitions[(source, label)] = indices[target_subset]
    return DFA(0, frozenset(finals), tuple(symbols),
               tuple(label for label in nfa.alphabet if label != EPSILON),
               symbols, transitions, tuple(subsets), char_classes,
               indices.get(frozenset()))


def _set(states, prefix: str) -> str:
    return "{" + ",".join(prefix + str(i) for i in sorted(states)) + "}"


def _char_set(chars: frozenset[str]) -> str:
    """Compact ranges for legends; range bounds use escaped display labels."""
    codes = sorted(ord(c) for c in chars)
    if not codes:
        return "{}"
    runs = []
    start = end = codes[0]
    for code in codes[1:] + [None]:
        if code is not None and code == end + 1:
            end = code
            continue
        a, b = display_char(chr(start)), display_char(chr(end))
        runs.append(a if start == end else a + ".." + b)
        if code is not None:
            start = end = code
    return "{" + ",".join(runs) + "}"


def format_automata(nfa: NFA, dfa: DFA) -> str:
    lines = ["AFND", "Q=" + _set(range(nfa.state_count), "q"),
             "Σ={" + ",".join(nfa.alphabet) + "}", "Inicial=q0",
             "F=" + _set(nfa.finals, "q")]
    for state in range(nfa.state_count):
        for label in nfa.alphabet:
            targets = nfa.transitions.get((state, label))
            if targets:
                lines.append(f"q{state}|{label}|" + _set(targets, "q"))
    lines += ["", "AFD", "Q=" + _set(range(dfa.state_count), "Q"),
              "Σ={" + ",".join(dfa.source_alphabet) + "}",
              "Γ={" + ",".join(dfa.alphabet) + "}",
              "Inicial=Q0", "F=" + _set(dfa.finals, "Q"),
              "Γ: particiones disjuntas de ASCII; incluyen la clase residual."]
    for label, chars in dfa.symbol_sets.items():
        lines.append(label + "=" + _char_set(chars))
    lines.append("Subconjuntos del AFND:")
    for state, subset in enumerate(dfa.subsets):
        lines.append(f"Q{state}=" + _set(subset, "q"))
    for state in range(dfa.state_count):
        for label in dfa.alphabet:
            lines.append(f"Q{state}|{label}|Q{dfa.transitions[(state, label)]}")
    return "\n".join(lines)


@dataclass
class CompiledRegex:
    pattern: str
    nfa: NFA
    dfa: DFA

    def match(self, text: str) -> MatchResult:
        return self.dfa.match(text)

    def accepts(self, text: str) -> bool:
        return self.dfa.accepts(text)

    def format_tables(self) -> str:
        return format_automata(self.nfa, self.dfa)

    def to_dict(self) -> dict:
        return {
            "expression": self.pattern,
            "universe": "ASCII 0..127",
            "nfa": {
                "states": [f"q{i}" for i in range(self.nfa.state_count)],
                "alphabet": list(self.nfa.alphabet), "initial": "q0",
                "finals": [f"q{i}" for i in sorted(self.nfa.finals)],
                "symbol_sets": {label: sorted(chars, key=ord) for label, chars in self.nfa.symbol_sets.items()},
                "transitions": [{"source": f"q{s}", "symbol": label,
                                 "targets": [f"q{t}" for t in sorted(targets)]}
                                for (s, label), targets in sorted(self.nfa.transitions.items())]},
            "dfa": {
                "states": [f"Q{i}" for i in range(self.dfa.state_count)],
                "source_alphabet": list(self.dfa.source_alphabet),
                "alphabet": list(self.dfa.alphabet), "initial": "Q0",
                "finals": [f"Q{i}" for i in sorted(self.dfa.finals)],
                "dead_state": None if self.dfa.dead_state is None else f"Q{self.dfa.dead_state}",
                "partitions": {label: sorted(chars, key=ord) for label, chars in self.dfa.symbol_sets.items()},
                "subsets": {f"Q{i}": [f"q{q}" for q in sorted(subset)]
                            for i, subset in enumerate(self.dfa.subsets)},
                "transitions": [{"source": f"Q{s}", "symbol": label, "target": f"Q{target}"}
                                for (s, label), target in sorted(self.dfa.transitions.items())]}}

    def to_dot(self, kind: str = "dfa") -> str:
        import json
        if kind not in ("nfa", "dfa"):
            raise ValueError("kind debe ser 'nfa' o 'dfa'.")
        machine = self.nfa if kind == "nfa" else self.dfa
        prefix = "q" if kind == "nfa" else "Q"
        lines = ["digraph automata {", "  rankdir=LR;", "  node [shape=circle];",
                 "  start [shape=point];", f"  start -> {prefix}0;"]
        for final in sorted(machine.finals):
            lines.append(f"  {prefix}{final} [shape=doublecircle];")
        grouped: dict[tuple[int, int], list[str]] = {}
        for (source, label), targets in machine.transitions.items():
            actual = targets if kind == "nfa" else (targets,)
            for target in actual:
                grouped.setdefault((source, target), []).append(label)
        for (source, target), labels in sorted(grouped.items()):
            label = json.dumps(", ".join(labels), ensure_ascii=False)
            lines.append(f"  {prefix}{source} -> {prefix}{target} [label={label}];")
        if kind == "dfa":
            legend = "\n".join(label + "=" + _char_set(chars)
                                  for label, chars in self.dfa.symbol_sets.items())
            lines.append("  legend [shape=box,label=" + json.dumps(legend, ensure_ascii=False) + "];")
        lines.append("}")
        return "\n".join(lines) + "\n"


def compile_regex(pattern: str, max_dfa_states: int = 4096) -> CompiledRegex:
    parsed = parse_regex(pattern)
    nfa = thompson(parsed)
    return CompiledRegex(pattern, nfa, determinize(nfa, max_dfa_states))
