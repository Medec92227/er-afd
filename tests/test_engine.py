"""Lenguajes conocidos, invariantes y equivalencia independiente AFND/AFD."""

import ast
from functools import lru_cache
from itertools import product
from pathlib import Path
import unittest

from er_afd import compile_regex
from er_afd.parser import RegexSyntaxError

try:
    from .cases import CASES, DIFFERENTIAL_PATTERNS, INVALID_PATTERNS
except ImportError:
    from cases import CASES, DIFFERENTIAL_PATTERNS, INVALID_PATTERNS


@lru_cache(maxsize=128)
def compiled(pattern):
    return compile_regex(pattern)


def nfa_accepts(nfa, text):
    """Simulador de prueba independiente: no llama métodos del producto."""
    def closure(states):
        found = set(states)
        pending = list(states)
        while pending:
            current = pending.pop()
            for target in nfa.transitions.get((current, "ε"), ()):
                if target not in found:
                    found.add(target)
                    pending.append(target)
        return found

    current = closure({nfa.start})
    for char in text:
        destinations = set()
        for (source, label), targets in nfa.transitions.items():
            if source in current and label != "ε" and char in nfa.symbol_sets[label]:
                destinations.update(targets)
        current = closure(destinations)
    return bool(current.intersection(nfa.finals))


def differential_samples():
    alphabet = "abc1 "
    yield ""
    for length in range(1, 5):
        for chars in product(alphabet, repeat=length):
            yield "".join(chars)


class KnownLanguageTests(unittest.TestCase):
    def test_independent_known_language_cases(self):
        for case in CASES:
            with self.subTest(pattern=case.pattern, text=repr(case.text), family=case.family):
                result = compiled(case.pattern)
                self.assertEqual(result.accepts(case.text), case.expected)
                self.assertEqual(result.dfa.accepts(case.text), case.expected)

    def test_malformed_patterns_raise_syntax_error(self):
        for pattern in ["", "()", "a()b", *INVALID_PATTERNS]:
            with self.subTest(pattern=pattern):
                with self.assertRaises(RegexSyntaxError):
                    compile_regex(pattern)

    def test_non_ascii_input_is_reported(self):
        for pattern in [".*", "[^a]", "a*"]:
            for text in ["é", "año", "漢", "😀"]:
                with self.subTest(pattern=pattern, text=text):
                    with self.assertRaises(ValueError):
                        compiled(pattern).accepts(text)

    def test_only_specified_operators_have_special_meaning(self):
        for literal in ["+", "?", "^", "$", "{", "}"]:
            with self.subTest(literal=literal):
                self.assertTrue(compiled(literal).accepts(literal))
                self.assertFalse(compiled(literal).accepts(""))

    def test_kleene_handles_long_input_without_recursion(self):
        self.assertTrue(compiled("a*").accepts("a" * 20000))
        self.assertFalse(compiled("a*").accepts("a" * 20000 + "b"))

    def test_hyphen_at_class_edge_is_literal(self):
        for pattern in ["[-a]", "[a-]"]:
            for char in ["-", "a"]:
                self.assertTrue(compiled(pattern).accepts(char))
            self.assertFalse(compiled(pattern).accepts("b"))


class AutomatonInvariantTests(unittest.TestCase):
    def test_initial_states_and_all_destinations_are_declared(self):
        for pattern in DIFFERENTIAL_PATTERNS:
            with self.subTest(pattern=pattern):
                result = compiled(pattern)
                for automaton in [result.nfa, result.dfa]:
                    self.assertEqual(automaton.start, 0)
                    self.assertGreater(automaton.state_count, 0)
                    declared = set(range(automaton.state_count))
                    self.assertTrue(set(automaton.finals).issubset(declared))
                    for (source, label), targets in automaton.transitions.items():
                        self.assertIn(source, declared)
                        self.assertIn(label, automaton.alphabet)
                        if isinstance(targets, int):
                            self.assertIn(targets, declared)
                        else:
                            self.assertTrue(set(targets).issubset(declared))

    def test_alphabet_preserves_source_order_and_epsilon_rule(self):
        self.assertEqual(compiled("bεa.b").nfa.alphabet, ("b", "ε", "a", "."))
        self.assertEqual(compiled("bεa.b").dfa.source_alphabet, ("b", "a", "."))
        self.assertEqual(compiled("baab").nfa.alphabet, ("b", "a", "ε"))
        self.assertEqual(compiled("baab").dfa.source_alphabet, ("b", "a"))
        self.assertEqual(compiled("ε").nfa.alphabet, ("ε",))
        self.assertEqual(compiled("ε").dfa.source_alphabet, ())

    def test_dfa_partition_classes_are_disjoint(self):
        for pattern in DIFFERENTIAL_PATTERNS:
            with self.subTest(pattern=pattern):
                dfa = compiled(pattern).dfa
                self.assertNotIn("ε", dfa.alphabet)
                seen = set()
                for label in dfa.alphabet:
                    members = set(dfa.symbol_sets[label])
                    self.assertTrue(members)
                    self.assertFalse(seen.intersection(members))
                    self.assertTrue(all(ord(char) < 128 for char in members))
                    seen.update(members)

    def test_dfa_transition_matrix_is_complete_for_its_alphabet(self):
        for pattern in DIFFERENTIAL_PATTERNS:
            with self.subTest(pattern=pattern):
                dfa = compiled(pattern).dfa
                self.assertEqual(len(dfa.transitions), dfa.state_count * len(dfa.alphabet))
                for state in range(dfa.state_count):
                    for label in dfa.alphabet:
                        self.assertIn((state, label), dfa.transitions)

    def test_subset_acceptance_matches_nfa_final_membership(self):
        for pattern in DIFFERENTIAL_PATTERNS:
            with self.subTest(pattern=pattern):
                result = compiled(pattern)
                self.assertEqual(len(result.dfa.subsets), result.dfa.state_count)
                self.assertIn(0, result.dfa.subsets[0])
                self.assertEqual(len(set(result.dfa.subsets)), result.dfa.state_count)
                for index, states in enumerate(result.dfa.subsets):
                    self.assertEqual(index in result.dfa.finals, bool(states & result.nfa.finals))

    def test_trace_uses_actual_input_characters_and_starts_at_Q0(self):
        result = compiled("a.*b").match("a b")
        self.assertTrue(result.accepted)
        self.assertEqual(len(result.trace), 3)
        self.assertEqual(result.trace[0].source, 0)
        self.assertEqual("".join(step.symbol for step in result.trace), "a b")
        for previous, next_step in zip(result.trace, result.trace[1:]):
            self.assertEqual(previous.target, next_step.source)
        self.assertEqual(result.trace[-1].target, result.final_state)

    def test_dfa_state_budget_fails_explicitly(self):
        with self.assertRaises(ValueError):
            compile_regex("ab", max_dfa_states=1)

    def test_core_does_not_import_a_regex_engine(self):
        package = Path(__file__).resolve().parents[1] / "er_afd"
        for path in package.glob("*.py"):
            with self.subTest(path=path.name):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.update(item.name.split(".")[0] for item in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imports.add(node.module.split(".")[0])
                self.assertFalse(imports & {"re", "regex", "fnmatch"})


class DifferentialTests(unittest.TestCase):
    def test_dfa_equals_independent_nfa_simulation(self):
        samples = tuple(differential_samples())
        for pattern in DIFFERENTIAL_PATTERNS:
            result = compiled(pattern)
            for text in samples:
                with self.subTest(pattern=pattern, text=repr(text)):
                    self.assertEqual(result.accepts(text), nfa_accepts(result.nfa, text))


if __name__ == "__main__":
    unittest.main()
