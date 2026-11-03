"""Máxima longitud, prioridad, posiciones y errores de tokenización."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from er_afd.lexer import LexerError, compile_rules, tokenize


ROOT = Path(__file__).resolve().parents[1]
BASE_RULES = [
    {"name": "IF", "regex": "if"},
    {"name": "ID", "regex": "[a-zA-Z_][a-zA-Z_0-9]*"},
    {"name": "INT", "regex": r"\N\N*"},
    {"name": "SPACE", "regex": r"[\h20\h09\h0A\h0D][\h20\h09\h0A\h0D]*", "skip": True},
    {"name": "EQ", "regex": "="},
]


class LexerTests(unittest.TestCase):
    def test_longest_match_wins_then_first_rule_breaks_tie(self):
        rules = compile_rules(BASE_RULES)
        actual = tokenize(rules, "if ifx x=123")
        self.assertEqual([(t.type, t.value) for t in actual],
                         [("IF", "if"), ("ID", "ifx"), ("ID", "x"), ("EQ", "="), ("INT", "123")])

    def test_first_rule_controls_equal_length_tie(self):
        first = compile_rules([{"name": "A", "regex": "ab"}, {"name": "B", "regex": "a."}])
        second = compile_rules([{"name": "B", "regex": "a."}, {"name": "A", "regex": "ab"}])
        self.assertEqual(tokenize(first, "ab")[0].type, "A")
        self.assertEqual(tokenize(second, "ab")[0].type, "B")

    def test_failed_longer_candidate_backtracks_to_last_acceptance(self):
        rules = compile_rules([
            {"name": "ABC", "regex": "abc"}, {"name": "A", "regex": "a"},
            {"name": "B", "regex": "b"}, {"name": "X", "regex": "x"},
        ])
        self.assertEqual([(t.type, t.value) for t in tokenize(rules, "abx")],
                         [("A", "a"), ("B", "b"), ("X", "x")])

    def test_positions_count_skipped_characters_and_newlines(self):
        result = tokenize(compile_rules(BASE_RULES), "if\r\n  x=7")
        self.assertEqual([(t.type, t.start, t.end, t.line, t.column) for t in result],
                         [("IF", 0, 2, 1, 1), ("ID", 6, 7, 2, 3),
                          ("EQ", 7, 8, 2, 4), ("INT", 8, 9, 2, 5)])

    def test_empty_or_only_skipped_input_returns_no_tokens(self):
        rules = compile_rules(BASE_RULES)
        self.assertEqual(tokenize(rules, ""), [])
        self.assertEqual(tokenize(rules, " \t\r\n"), [])

    def test_nullable_rules_are_forbidden(self):
        for pattern in ["ε", "a*", "(a|ε)b*", ".*"]:
            with self.subTest(pattern=pattern):
                with self.assertRaises(LexerError):
                    compile_rules([{"name": "EMPTY", "regex": pattern}])

    def test_invalid_specifications_fail_explicitly(self):
        specs = [None, {}, [], ["bad"], [{}], [{"name": "", "regex": "a"}],
                 [{"name": "A", "regex": 123}], [{"name": "A", "regex": "a", "skip": "yes"}],
                 [{"name": "A", "regex": "a", "unknown": True}],
                 [{"name": "A", "regex": "a"}, {"name": "A", "regex": "b"}]]
        for specification in specs:
            with self.subTest(specification=specification):
                with self.assertRaises(ValueError):
                    compile_rules(specification)

    def test_unmatched_character_and_non_ascii_are_errors(self):
        rules = compile_rules(BASE_RULES)
        for text in ["x=1!", "niño", "😀"]:
            with self.subTest(text=text):
                with self.assertRaises(LexerError):
                    tokenize(rules, text)
        with self.assertRaises(LexerError):
            tokenize((), "a")

    def test_error_reports_exact_position(self):
        with self.assertRaises(LexerError) as error:
            tokenize(compile_rules(BASE_RULES), "if\n  !")
        self.assertIn("línea 2", str(error.exception))
        self.assertIn("columna 3", str(error.exception))
        self.assertIn("offset 5", str(error.exception))

    def test_cli_json_output_and_return_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            rules_path = Path(directory) / "rules.json"
            rules_path.write_text(json.dumps(BASE_RULES), encoding="utf-8")
            env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
            command = [sys.executable, "-m", "er_afd.lexer", "--rules", str(rules_path), "--text"]
            good = subprocess.run(command + ["if x=42"], cwd=ROOT, env=env, capture_output=True,
                                  text=True, encoding="utf-8", timeout=30)
            self.assertEqual(good.returncode, 0, good.stderr)
            tokens = json.loads(good.stdout)
            self.assertEqual([token["type"] for token in tokens], ["IF", "ID", "EQ", "INT"])
            bad = subprocess.run(command + ["!"], cwd=ROOT, env=env, capture_output=True,
                                 text=True, encoding="utf-8", timeout=30)
            self.assertEqual(bad.returncode, 2)
            self.assertNotIn("Traceback", bad.stderr)


if __name__ == "__main__":
    unittest.main()
