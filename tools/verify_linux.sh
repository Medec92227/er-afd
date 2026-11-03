#!/usr/bin/env bash
# Ejecutar con: bash tools/verify_linux.sh [directorio_nuevo_de_evidencias]
set -euo pipefail

if [[ "$(uname -s)" != Linux ]] || [[ "$(getconf LONG_BIT)" != 64 ]]; then
    printf 'Error: este verificador debe ejecutarse dentro de Linux de 64 bits.\n' >&2
    exit 2
fi
for required in python3 make; do
    if ! command -v "$required" >/dev/null 2>&1; then
        printf 'Error: falta %s; prepara Ubuntu antes de ejecutar la verificación.\n' "$required" >&2
        exit 2
    fi
done

PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd -- "$PROJECT_ROOT"
RUN_STAMP=$(date -u +%Y%m%dT%H%M%SZ)
EVIDENCE_DIR=${1:-"$PROJECT_ROOT/doc/evidencias/linux/$RUN_STAMP"}
mkdir -p -- "$(dirname -- "$EVIDENCE_DIR")"
# Una ejecución nunca sobrescribe la evidencia de otra.
mkdir -- "$EVIDENCE_DIR"
EVIDENCE_DIR=$(cd -- "$EVIDENCE_DIR" && pwd)
export ER_AFD_EVIDENCE_DIR="$EVIDENCE_DIR"
exec > >(tee "$EVIDENCE_DIR/transcripcion.log") 2>&1
trap 'run_status=$?; if (( run_status != 0 )); then printf "\nVerificación incompleta (código %s). Revisa %s\n" "$run_status" "$EVIDENCE_DIR"; fi' EXIT

record() {
    local label=$1 expected=$2 actual
    shift 2
    printf '\n[%s] ' "$label"
    printf '%q ' "$@"
    printf '\n'
    if "$@" >"$EVIDENCE_DIR/$label.log" 2>&1; then
        actual=0
    else
        actual=$?
    fi
    cat -- "$EVIDENCE_DIR/$label.log"
    printf 'Retorno observado: %s; esperado: %s\n' "$actual" "$expected"
    printf '%s\t%s\t%s\n' "$label" "$expected" "$actual" >>"$EVIDENCE_DIR/retornos.tsv"
    if [[ "$actual" != "$expected" ]]; then
        printf 'ERROR: el retorno de %s no coincide.\n' "$label" >&2
        exit 1
    fi
}

printf 'ER-AFD: verificación real en Linux, usuario sin root\n'
date -u --iso-8601=seconds
uname -a
id
python3 --version
make --version
if [[ -r /etc/os-release ]]; then
    cat /etc/os-release
fi

python3 - <<'PY'
from pathlib import Path
import hashlib
import json
import os
import platform
import sys

out = Path(os.environ["ER_AFD_EVIDENCE_DIR"])
pdf_paths = [Path("doc") / name for name in
             ("Reporte_tecnico.pdf", "Manual_usuario.pdf", "Casos_de_prueba.pdf")]
pdf_hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in pdf_paths}
(out / "pdf_antes_clean.json").write_text(json.dumps(pdf_hashes, indent=2) + "\n", encoding="utf-8")
environment = {"system": platform.system(), "platform": platform.platform(),
               "machine": platform.machine(), "python": platform.python_version(),
               "executable": sys.executable, "uid": os.getuid()}
if environment["uid"] == 0:
    raise SystemExit("Ejecuta las pruebas como usuario regular, no mediante sudo.")
(out / "entorno.json").write_text(json.dumps(environment, indent=2) + "\n", encoding="utf-8")
PY

record 01_config 0 make config
record 02_build 0 make build
record 03_tests 0 make test
record 04_make_run 0 make run 'ER=(a|b)*abb' 'CADENA=aabb'
record 05_aceptada 1 python3 dist/er-afd '(a|b)*abb' 'aabb'
record 06_rechazada 0 python3 dist/er-afd '(a|b)*abb' 'aab'
record 07_error_sintaxis 2 python3 dist/er-afd '[z-a]' 'a'
record 08_vacia 1 python3 dist/er-afd 'ε' ''
record 09_json 1 python3 dist/er-afd '(a|b)*abb' 'aabb' --json
record 10_dot 1 python3 dist/er-afd '(a|b)*abb' 'aabb' --dot "$EVIDENCE_DIR/ejemplo"
printf 'aabb' >"$EVIDENCE_DIR/entrada_sin_salto.txt"
record 11_archivo 1 python3 dist/er-afd '(a|b)*abb' --file "$EVIDENCE_DIR/entrada_sin_salto.txt"
record 12_lexer 0 python3 dist/er-lex --rules examples/reglas.json --file examples/programa.txt
record 13_metricas 0 python3 -m tests.run_validation --output "$EVIDENCE_DIR/metricas_linux.json"

python3 - <<'PY'
from pathlib import Path
import json
import os

out = Path(os.environ["ER_AFD_EVIDENCE_DIR"])
simulation = json.loads((out / "09_json.log").read_text(encoding="utf-8"))
assert simulation["accepted"] is True and simulation["exit_code"] == 1
assert len(simulation["trace"]) == 4 and simulation["trace"][0]["source"] == "Q0"
tokens = json.loads((out / "12_lexer.log").read_text(encoding="utf-8"))
assert [token["type"] for token in tokens] == [
    "SI", "IDENTIFICADOR", "IGUAL", "NUMERO", "SUMA", "IDENTIFICADOR", "PUNTO_COMA"]
assert "digraph" in (out / "ejemplo.afnd.dot").read_text(encoding="utf-8")
assert "digraph" in (out / "ejemplo.afd.dot").read_text(encoding="utf-8")
metrics = json.loads((out / "metricas_linux.json").read_text(encoding="utf-8"))
assert metrics["environment"]["platform"].startswith("Linux")
assert metrics["unit_tests"]["passed"] and metrics["unit_tests"]["run"] >= 39
assert not metrics["known_language"]["failures"]
assert metrics["known_language"]["cases"] >= 1499
assert not metrics["differential_nfa_dfa"]["mismatches"]
assert metrics["differential_nfa_dfa"]["comparisons"] >= 20306
print("JSON, tokens, DOT y métricas: comprobados.")
PY

record 14_clean 0 make clean
python3 - <<'PY'
from pathlib import Path
import hashlib
import json
import os

out = Path(os.environ["ER_AFD_EVIDENCE_DIR"])
assert not Path("dist/er-afd").exists() and not Path("dist/er-lex").exists()
assert Path("er_afd/automata.py").is_file()
assert (out / "metricas_linux.json").is_file()
for filename, expected in json.loads((out / "pdf_antes_clean.json").read_text(encoding="utf-8")).items():
    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected, filename
print("make clean conservó código, PDF y evidencia.")
PY
record 15_rebuild 0 make build
record 16_rebuild_aceptada 1 python3 dist/er-afd 'a*b' 'aaab'

python3 - <<'PY'
from datetime import datetime, timezone
from pathlib import Path
import json
import os

out = Path(os.environ["ER_AFD_EVIDENCE_DIR"])
metrics = json.loads((out / "metricas_linux.json").read_text(encoding="utf-8"))
checks = []
for line in (out / "retornos.tsv").read_text(encoding="utf-8").splitlines():
    label, expected, actual = line.split("\t")
    checks.append({"check": label, "expected": int(expected), "actual": int(actual)})
assert len(checks) == 16 and all(item["expected"] == item["actual"] for item in checks)
summary = {"completed": True, "completed_at_utc": datetime.now(timezone.utc).isoformat(),
           "environment": json.loads((out / "entorno.json").read_text(encoding="utf-8")),
           "checks": checks, "unit_tests": metrics["unit_tests"],
           "known_language_cases": metrics["known_language"]["cases"],
           "differential_comparisons": metrics["differential_nfa_dfa"]["comparisons"],
           "note": "Resultados de esta ejecución. Las capturas de pantalla se añaden por separado."}
(out / "resultado.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"completed": True, "unit_tests": summary["unit_tests"]["run"],
                  "known_language_cases": summary["known_language_cases"],
                  "differential_comparisons": summary["differential_comparisons"]}, ensure_ascii=False))
PY
printf '\nVERIFICACION LINUX COMPLETADA. Evidencias: %s\n' "$EVIDENCE_DIR"
