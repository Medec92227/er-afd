"""Pruebas de la línea de comando er-afd."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    return subprocess.run(
        [sys.executable, "-m", "er_afd", *args],
        cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=30,
    )


class CLITests(unittest.TestCase):
    def test_accepted_returns_one_and_exact_final_message(self):
        result = run_cli("(a|b)*abb", "aabb")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout.rstrip().splitlines()[-1], "Cadena aceptada")
        self.assertIn("AFND", result.stdout)
        self.assertIn("AFD", result.stdout)

    def test_output_follows_the_project_format(self):
        result = run_cli("ab*", "abb")
        self.assertEqual(result.returncode, 1, result.stderr)
        expected = """AFND
Q={q0,q1,q2,q3,q4,q5}
Σ={a,b,ε}
F={q5}
q0|a|{q1}
q1|ε|{q4}
q2|b|{q3}
q3|ε|{q2,q5}
q4|ε|{q2,q5}

AFD
Q={Q0,Q1,Q2}
Σ={a,b}
F={Q1,Q2}
Q0|a|Q1
Q1|b|Q2
Q2|b|Q2

Q0|a|Q1
Q1|b|Q2
Q2|b|Q2
Cadena aceptada
"""
        self.assertEqual(result.stdout, expected)

    def test_verbose_adds_subsets(self):
        result = run_cli("ab*", "abb", "--verbose")
        self.assertIn("Q1={q1,q2,q4,q5}", result.stdout)

    def test_rejected_returns_zero_and_exact_final_message(self):
        result = run_cli("ab", "aa")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.rstrip().splitlines()[-1], "Cadena rechazada")

    def test_syntax_error_returns_two(self):
        result = run_cli("[z-a]", "z")
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.strip())
        self.assertNotIn("Traceback", result.stderr)

    def test_non_ascii_argument_returns_two(self):
        result = run_cli(".*", "niño")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_arguments_return_two(self):
        self.assertEqual(run_cli().returncode, 2)

    def test_empty_string_can_be_passed_as_positional_argument(self):
        result = run_cli("ε", "")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("Cadena aceptada", result.stdout)

    def test_spaces_and_literal_escape_survive_argument_transport(self):
        for pattern in ["hola mundo", r"hola\ mundo", r"hola\h20mundo"]:
            with self.subTest(pattern=pattern):
                result = run_cli(pattern, "hola mundo")
                self.assertEqual(result.returncode, 1, result.stderr)

    def test_json_mode_emits_valid_json_without_text_tables(self):
        result = run_cli("--json", "a|.", "a")
        self.assertEqual(result.returncode, 1, result.stderr)
        parsed = json.loads(result.stdout)
        self.assertIsInstance(parsed, dict)
        self.assertNotIn("Cadena aceptada\n", result.stdout)
        self.assertEqual(parsed["expression"], "a|.")
        self.assertTrue(parsed["accepted"])
        self.assertEqual(parsed["exit_code"], 1)
        self.assertEqual(parsed["nfa"]["initial"], "q0")
        self.assertEqual(parsed["dfa"]["initial"], "Q0")
        self.assertEqual(parsed["trace"][0]["symbol"], "a")

    def test_json_errors_stay_machine_readable(self):
        result = run_cli("--json", "(", "a")
        self.assertEqual(result.returncode, 2)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["exit_code"], 2)
        self.assertTrue(parsed["error"])

    def test_dot_exports_both_automata(self):
        with tempfile.TemporaryDirectory() as temp:
            prefix = Path(temp) / "diagramas" / "demo"
            result = run_cli("a|b", "a", "--dot", str(prefix))
            self.assertEqual(result.returncode, 1, result.stderr)
            for suffix, state in [(".afnd.dot", "q0"), (".afd.dot", "Q0")]:
                path = Path(str(prefix) + suffix)
                content = path.read_text(encoding="utf-8")
                self.assertIn("digraph", content)
                self.assertIn(state, content)
                self.assertIn("doublecircle", content)

    def test_state_limit_error_returns_two(self):
        result = run_cli("ab", "ab", "--max-states", "1")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    def test_input_source_is_unambiguous(self):
        result = run_cli("a", "a", "--file", "unused.txt")
        self.assertEqual(result.returncode, 2)

    def test_file_mode_reads_exact_content(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "texto.txt"
            path.write_bytes(b"ab\n")
            result = run_cli(r"ab\h0A", "--file", str(path))
            self.assertEqual(result.returncode, 1, result.stderr)
            result = run_cli("ab", "--file", str(path))
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_file_mode_reports_non_ascii_and_missing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "texto.txt"
            path.write_text("á", encoding="utf-8")
            result = run_cli(".*", "--file", str(path))
            self.assertEqual(result.returncode, 2)
            result = run_cli(".*", "--file", str(Path(temp) / "ausente.txt"))
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
