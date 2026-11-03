"""Ejecuta la suite y escribe métricas verificables, sin usar regex.

Uso: python -m tests.run_validation --output doc/evidencias/metricas.json
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sys
import unittest

from .cases import CASES, DIFFERENTIAL_PATTERNS, INVALID_PATTERNS
from .test_engine import compiled, differential_samples, nfa_accepts


def measure():
    confusion = Counter(tp=0, tn=0, fp=0, fn=0)
    family_counts = Counter()
    failures = []
    for case in CASES:
        actual = compiled(case.pattern).accepts(case.text)
        confusion["tp" if actual and case.expected else
                  "fp" if actual else "fn" if case.expected else "tn"] += 1
        family_counts[case.family] += 1
        if actual != case.expected:
            failures.append({"regex": case.pattern, "text": repr(case.text),
                             "expected": case.expected, "actual": actual})
    comparison_count = 0
    mismatches = []
    samples = tuple(differential_samples())
    for pattern in DIFFERENTIAL_PATTERNS:
        result = compiled(pattern)
        for sample in samples:
            comparison_count += 1
            dfa_result = result.accepts(sample)
            nfa_result = nfa_accepts(result.nfa, sample)
            if dfa_result != nfa_result:
                mismatches.append({"regex": pattern, "text": repr(sample)})
    total = sum(confusion.values())
    return {
        "known_language": {
            "cases": total, "correct": confusion["tp"] + confusion["tn"],
            "accuracy": (confusion["tp"] + confusion["tn"]) / total,
            "precision": confusion["tp"] / (confusion["tp"] + confusion["fp"]),
            "recall": confusion["tp"] / (confusion["tp"] + confusion["fn"]),
            "confusion_matrix": dict(confusion), "families": dict(family_counts),
            "failures": failures,
        },
        "differential_nfa_dfa": {
            "patterns": len(DIFFERENTIAL_PATTERNS),
            "strings_per_pattern": len(samples),
            "alphabet": "abc1 ", "max_length": 4,
            "comparisons": comparison_count,
            "agreements": comparison_count - len(mismatches),
            "agreement_rate": (comparison_count - len(mismatches)) / comparison_count,
            "mismatches": mismatches,
        },
        "methodology": (
            "Oráculos manuales independientes para casos positivos y negativos; "
            "11 clases contrastadas con los 128 caracteres ASCII. Simulación AFND "
            "independiente frente al AFD sobre todos los textos de longitud 0..4 "
            "del alfabeto indicado. Las métricas describen esta muestra finita; "
            "no demuestran precisión universal ni estiman datos reales no muestreados."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern="test_*.py")
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "unit_tests": {"run": outcome.testsRun, "failures": len(outcome.failures),
                       "errors": len(outcome.errors), "skipped": len(outcome.skipped),
                       "passed": outcome.wasSuccessful()},
        **measure(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Métricas guardadas en", args.output)
    return 0 if (outcome.wasSuccessful() and not report["known_language"]["failures"]
                 and not report["differential_nfa_dfa"]["mismatches"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
