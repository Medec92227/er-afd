#!/usr/bin/env bash
cd /home/erafd/er-afd
export EVIDENCE='/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z'
exec > >(tee '/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z/capturas/05_lexer_y_escapes.log') 2>&1
printf '\033[2J\033[H'
printf 'Ubuntu: 05_lexer_y_escapes\n\n'
set -x
./dist/er-lex --rules examples/reglas.json --file examples/programa.txt > "$EVIDENCE/capturas/05_tokens.json"
estado=$?
python3 -c 'import json,os; from pathlib import Path; tokens=json.loads((Path(os.environ["EVIDENCE"])/"capturas/05_tokens.json").read_text()); [print(t["type"],repr(t["value"]),t["start"],t["end"]) for t in tokens]'
printf 'Retorno del lexer: %s\n' "$estado"
./dist/er-afd 'hola\ mundo' 'hola mundo' --json > "$EVIDENCE/capturas/05_espacio.json"
estado=$?
python3 -c 'import json,os; from pathlib import Path; r=json.loads((Path(os.environ["EVIDENCE"])/"capturas/05_espacio.json").read_text()); print("Espacio escapado, aceptada:",r["accepted"])'
printf 'Retorno con espacio escapado: %s (1 = aceptada)\n' "$estado"

set +x
printf '\nCaptura terminada. Evidencia guardada.\n'
touch '/home/erafd/er-afd/doc/evidencias/linux/20261102T180611Z/capturas/05_lexer_y_escapes.done'
while :; do sleep 3600; done
