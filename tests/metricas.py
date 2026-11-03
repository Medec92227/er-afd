"""Calcula las métricas de precisión del reconocedor.

Uso: python3 -m tests.metricas [--output doc/metricas.json]

1. Casos con resultado esperado escrito a mano (tests/cases.py).
2. Comparación del AFD contra una simulación directa del AFND para todas
   las cadenas de longitud 0 a 4 sobre el alfabeto "abc1 ".
"""

import argparse
from collections import Counter
import json
from pathlib import Path

from .cases import CASES, DIFFERENTIAL_PATTERNS
from .test_engine import compiled, differential_samples, nfa_accepts


def measure():
    confusion = Counter(tp=0, tn=0, fp=0, fn=0)
    failures = []
    for case in CASES:
        actual = compiled(case.pattern).accepts(case.text)
        if actual and case.expected:
            confusion["tp"] += 1
        elif actual:
            confusion["fp"] += 1
        elif case.expected:
            confusion["fn"] += 1
        else:
            confusion["tn"] += 1
        if actual != case.expected:
            failures.append({"regex": case.pattern, "texto": case.text, "esperado": case.expected})

    samples = tuple(differential_samples())
    comparisons = 0
    mismatches = []
    for pattern in DIFFERENTIAL_PATTERNS:
        result = compiled(pattern)
        for sample in samples:
            comparisons += 1
            if result.accepts(sample) != nfa_accepts(result.nfa, sample):
                mismatches.append({"regex": pattern, "texto": sample})

    total = sum(confusion.values())
    correct = confusion["tp"] + confusion["tn"]
    return {
        "casos_esperados": {
            "total": total,
            "correctos": correct,
            "exactitud": round(correct / total, 4),
            "precision": round(confusion["tp"] / max(confusion["tp"] + confusion["fp"], 1), 4),
            "exhaustividad": round(confusion["tp"] / max(confusion["tp"] + confusion["fn"], 1), 4),
            "matriz_confusion": dict(confusion),
            "fallos": failures,
        },
        "afnd_vs_afd": {
            "expresiones": len(DIFFERENTIAL_PATTERNS),
            "cadenas_por_expresion": len(samples),
            "comparaciones": comparisons,
            "coincidencias": comparisons - len(mismatches),
            "diferencias": mismatches,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Métricas de precisión de ER-AFD.")
    parser.add_argument("--output", type=Path, help="Guardar el resultado como JSON.")
    args = parser.parse_args()
    report = measure()
    known, diff = report["casos_esperados"], report["afnd_vs_afd"]
    print(f"Casos con resultado esperado: {known['correctos']}/{known['total']} "
          f"(exactitud {known['exactitud']:.2%})")
    print(f"  VP={known['matriz_confusion']['tp']}  VN={known['matriz_confusion']['tn']}  "
          f"FP={known['matriz_confusion']['fp']}  FN={known['matriz_confusion']['fn']}")
    print(f"AFD contra AFND: {diff['coincidencias']}/{diff['comparaciones']} coincidencias "
          f"en {diff['expresiones']} expresiones")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Guardado en", args.output)
    return 0 if not known["fallos"] and not diff["diferencias"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
