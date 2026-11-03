#!/usr/bin/env bash
cd /home/erafd/er-afd
export EVIDENCE='/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z'
exec > >(tee '/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z/capturas/01_entorno.log') 2>&1
printf '\033[2J\033[H'
printf 'Ubuntu: 01_entorno\n\n'
set -x
cat /etc/os-release | head -n 6
uname -m
getconf LONG_BIT
id
python3 --version
make --version | head -n 1
timedatectl show --property=Timezone --value

set +x
printf '\nCaptura terminada. Evidencia guardada.\n'
touch '/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z/capturas/01_entorno.done'
while :; do sleep 3600; done
