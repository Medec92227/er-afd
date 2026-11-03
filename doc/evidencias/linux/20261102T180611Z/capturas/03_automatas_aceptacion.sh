#!/usr/bin/env bash
cd /home/erafd/er-afd
export EVIDENCE='/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z'
exec > >(tee '/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z/capturas/03_automatas_aceptacion.log') 2>&1
printf '\033[2J\033[H'
printf 'Ubuntu: 03_automatas_aceptacion\n\n'
set -x
./dist/er-afd 'a' 'a'
estado=$?
printf 'Retorno: %s (1 = aceptada)\n' "$estado"

set +x
printf '\nCaptura terminada. Evidencia guardada.\n'
touch '/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z/capturas/03_automatas_aceptacion.done'
while :; do sleep 3600; done
