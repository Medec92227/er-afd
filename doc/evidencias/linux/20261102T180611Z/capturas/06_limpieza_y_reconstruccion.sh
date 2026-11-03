#!/usr/bin/env bash
cd /home/erafd/er-afd
export EVIDENCE='/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z'
exec > >(tee '/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z/capturas/06_limpieza_y_reconstruccion.log') 2>&1
printf '\033[2J\033[H'
printf 'Ubuntu: 06_limpieza_y_reconstruccion\n\n'
set -x
make clean
test -f er_afd/automata.py && test -f doc/Reporte_tecnico.pdf && test -f "$EVIDENCE/resultado.json" && echo 'Fuentes, PDF y evidencias conservados'
make build
./dist/er-afd 'a*b' 'aaab' > "$EVIDENCE/capturas/06_reconstruccion_aceptada.log"
estado=$?
tail -n 5 "$EVIDENCE/capturas/06_reconstruccion_aceptada.log"
printf 'Retorno tras reconstruir: %s (1 = aceptada)\n' "$estado"

set +x
printf '\nCaptura terminada. Evidencia guardada.\n'
touch '/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z/capturas/06_limpieza_y_reconstruccion.done'
while :; do sleep 3600; done
