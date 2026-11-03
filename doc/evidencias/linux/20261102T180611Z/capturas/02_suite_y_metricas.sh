#!/usr/bin/env bash
cd /home/erafd/er-afd
export EVIDENCE='/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z'
exec > >(tee '/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z/capturas/02_suite_y_metricas.log') 2>&1
printf '\033[2J\033[H'
printf 'Ubuntu: 02_suite_y_metricas\n\n'
set -x
make test > "$EVIDENCE/capturas/02_suite_completa.log" 2>&1
estado=$?
tail -n 8 "$EVIDENCE/capturas/02_suite_completa.log"
printf 'Retorno de make test: %s\n' "$estado"
python3 -c 'import json,os; from pathlib import Path; r=json.loads((Path(os.environ["EVIDENCE"])/"resultado.json").read_text()); print("Verificador completado:", r["completed"]); print("Comprobaciones:",len(r["checks"])); print("Pruebas unitarias:",r["unit_tests"]); print("Casos con oraculo:",r["known_language_cases"]); print("Comparaciones AFND/AFD:",r["differential_comparisons"])'

set +x
printf '\nCaptura terminada. Evidencia guardada.\n'
touch '/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z/capturas/02_suite_y_metricas.done'
while :; do sleep 3600; done
