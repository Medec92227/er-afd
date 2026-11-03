#!/usr/bin/env bash
cd /home/erafd/er-afd
export EVIDENCE='/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z'
exec > >(tee '/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z/capturas/04_rechazo_y_error.log') 2>&1
printf '\033[2J\033[H'
printf 'Ubuntu: 04_rechazo_y_error\n\n'
set -x
./dist/er-afd 'a' 'b' > "$EVIDENCE/capturas/04_rechazo_completo.log"
estado=$?
tail -n 4 "$EVIDENCE/capturas/04_rechazo_completo.log"
printf 'Retorno: %s (0 = rechazada)\n' "$estado"
./dist/er-afd '[z-a]' 'a'
estado=$?
printf 'Retorno: %s (2 = error de sintaxis)\n' "$estado"
./dist/er-afd 'ε' '' --json > "$EVIDENCE/capturas/04_epsilon.json"
estado=$?
python3 -c 'import json,os; from pathlib import Path; r=json.loads((Path(os.environ["EVIDENCE"])/"capturas/04_epsilon.json").read_text()); print("Epsilon con cadena vacia:",r["accepted"])'
printf 'Retorno epsilon con cadena vacia: %s (1 = aceptada)\n' "$estado"

set +x
printf '\nCaptura terminada. Evidencia guardada.\n'
touch '/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z/capturas/04_rechazo_y_error.done'
while :; do sleep 3600; done
