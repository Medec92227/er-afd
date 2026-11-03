# Guion de defensa: 10 minutos

Ensayar con el mismo entorno y la misma carpeta que se usarán ante el profesor. Los resultados siguientes corresponden a la implementación y a las evidencias incluidas; incluyen una ejecución real en Ubuntu 26.04.1 LTS x86_64, con Python 3.14.4 y GNU Make 4.4.1. Los registros están en `doc/evidencias/linux/20261102T180611Z/`.

Repositorio público de entrega: [Medec92227/er-afd](https://github.com/Medec92227/er-afd), rama `main`. El repositorio reúne los fuentes, Makefile, pruebas, tres PDF universitarios y evidencia real de Ubuntu.

## Minutos 0 a 2: demostración en vivo

Presentación sugerida: «El programa recibe una ER y una cadena ASCII, construye primero un AFND con Thompson, después un AFD por subconjuntos y finalmente evalúa la cadena mediante la matriz del AFD».

Preparar antes de la exposición:

```sh
make config
make build
export PATH="$PWD/dist:$PATH"
```

Mostrar aceptación y explicar el código de salida especial exigido por el enunciado:

```sh
er-afd '(a|b)*abb' 'aabb'
echo $?
```

El recorrido observado es:

```text
Q0|a|Q1
Q1|a|Q1
Q1|b|Q4
Q4|b|Q5
Cadena aceptada
```

El retorno es **1**. Después ejecutar `er-afd '(a|b)*abb' 'aaba'`: la cadena se rechaza y el retorno es **0**. Una ER inválida como `[z-a]` devuelve **2**, diferenciando un error de una cadena rechazada.

Mostrar brevemente la extensión con varias reglas:

```sh
er-lex --rules examples/reglas.json --file examples/programa.txt
```

Explicar: «Cada regla se convierte a un AFD; el tokenizador elige la coincidencia de mayor longitud y, ante empate, la primera regla. Los espacios se consumen con una regla `skip`».

## Minutos 2 a 5: diseño del autómata de la demostración

Utilizar el caso compuesto `(a|b)*abb`: combina unión, agrupación, cerradura y concatenación. Su lenguaje contiene cadenas formadas por `a` y `b` que terminan en `abb`.

1. `Parser` reconoce los átomos, la unión, la cerradura y la concatenación implícita, respetando sus prioridades. No ejecuta un motor de regex.
2. `thompson()` crea fragmentos con un inicio y un final. La unión y la cerradura agregan aristas épsilon; la concatenación conecta fragmentos mediante épsilon.
3. El AFND del ejemplo tiene **14 estados**, de `q0` a `q13`; comienza en **q0** y acepta en **q13**. La renumeración garantiza que el inicio sea q0 incluso si Thompson creó una envoltura al final.
4. `determinize()` calcula el épsilon-cierre inicial y explora subconjuntos. El AFD tiene **6 estados**, de `Q0` a `Q5`; comienza en **Q0**, acepta en **Q5** y usa **Q3** como pozo.
5. En este ejemplo `Σ={a,b}` y `Γ={a,b,C2}`. `C2` representa todos los otros caracteres ASCII. Sus transiciones llegan al pozo Q3, que tiene bucles para todas las clases.

Subconjuntos que conviene señalar en la salida:

```text
Q0={q0,q1,q3,q5,q7,q8}
Q3={}
Q5={q1,q3,q4,q5,q6,q7,q8,q13}
```

Q0 contiene todos los estados alcanzables desde q0 sin consumir caracteres. Q5 es de aceptación porque su subconjunto contiene q13. Q3 es el conjunto vacío y no puede alcanzar la aceptación.

Al explicar casos más amplios, usar `a|.` para mostrar el problema de etiquetas solapadas. Tanto `a` como `.` coinciden con la letra `a`; por ello se combinan los destinos antes de tomar el épsilon-cierre. Las particiones `Γ` evitan que una misma entrada tenga dos destinos en el AFD. Los rangos, conjuntos negativos y escapes especiales también se convierten a conjuntos explícitos de caracteres ASCII.

Señalar en el código `er_afd/parser.py`, `er_afd/automata.py` y `er_afd/cli.py`. La función `DFA.step()` consulta una transición de tabla; la simulación no vuelve a interpretar la ER.

## Minutos 5 a 7: pruebas y métricas

Como refuerzo separado del histórico, se ejecutaron 800 casos de lenguaje adicionales, 9 patrones inválidos y 25 procesos CLI en Ubuntu, sin fallos. El detalle y la separación de conteos están en `PRUEBAS_ADICIONALES.md`; la revisión de código está en `AUDITORIA_IMPLEMENTACION.md`. Los nueve patrones inválidos también se verifican dentro de los 25 procesos y no deben sumarse como procesos extra.

La evidencia reproducible de Ubuntu está en `doc/evidencias/linux/20261102T180611Z/metricas_linux.json`. Se utilizó **Ubuntu 26.04.1 LTS x86_64, Python 3.14.4 y GNU Make 4.4.1**, sin root. `doc/evidencias/metricas.json` conserva el histórico de Windows.

| Medición observada | Resultado |
| --- | --- |
| Pruebas de unittest | 39 ejecutadas, 0 fallos, 0 errores, 0 omitidas. |
| Casos con resultado esperado conocido | 1499 de 1499 correctos. |
| Verdaderos positivos | 710. |
| Verdaderos negativos | 789. |
| Falsos positivos / falsos negativos | 0 / 0. |
| Exactitud, precisión y sensibilidad en ese corpus | 100% cada una. |
| Comparaciones diferenciales AFND frente a AFD | 20306 de 20306 coinciden. |

Explicar cómo se obtuvieron:

- Los casos de lenguaje tienen oráculos explícitos, ejemplos aceptados y rechazados y verificaciones de once clases frente a los 128 caracteres ASCII.
- La comprobación diferencial compara un simulador de AFND independiente con el AFD para **26 patrones**, usando las **781** cadenas de longitud 0 a 4 del alfabeto de cinco caracteres `abc1 `, que incluye espacio. Son `26 × 781 = 20306` comparaciones.
- La suite verifica sintaxis inválida, aceptación completa, épsilon, solapamientos, clases, escapes, formato, códigos de retorno, archivos y la extensión léxica.

Reproducción:

```sh
make test
python3 -m tests.run_validation --output "$HOME/erafd-defensa-$(date -u +%Y%m%dT%H%M%SZ).json"
```

Frase de alcance: «Obtuvimos 100% en esta muestra finita. Esto no demuestra ausencia universal de errores ni estima una precisión sobre archivos reales que no hayamos muestreado. La comparación AFND/AFD tampoco sustituye los oráculos independientes, porque ambos parten del mismo parser y del AFND construido».

## Minutos 7 a 10: preguntas y respuestas

**¿Por qué el AFND tiene épsilon?** Thompson conecta alternativas, repeticiones y concatenaciones sin consumir entrada. El épsilon-cierre agrega todos los estados alcanzables mediante esas aristas.

**¿Qué representa un estado del AFD?** Un conjunto de posibles estados del AFND después de consumir un prefijo. El estado inicial es el épsilon-cierre de `{q0}` y un estado es final si su conjunto intersecta los finales del AFND.

**¿Por qué el AFD no tiene transiciones épsilon?** Cada transición del AFD consume un carácter y ya incorpora los épsilon-cierres antes o después del movimiento correspondiente.

**¿Por qué Q3 es pozo?** Representa el subconjunto vacío. Ninguna transición puede recuperar estados desde el conjunto vacío, de modo que permanece en Q3 y rechaza al terminar.

**¿Por qué se muestran Σ y Γ?** Σ conserva las etiquetas de la expresión en orden de aparición. Γ presenta las clases disjuntas utilizadas para una función de transición determinista y total sobre ASCII. La leyenda permite saber qué caracteres pertenecen a cada clase.

**¿Qué ocurre con `a|.`?** Se consideran ambos predicados al consumir `a` y se unen sus destinos. No se elige una alternativa por prioridad.

**¿La cadena se acepta si contiene un prefijo válido?** No. `er-afd` reconoce la cadena completa. El estado alcanzado después del último carácter debe ser final.

**¿Qué pasa con espacios y saltos de línea?** Los espacios pueden protegerse con comillas o escapes del shell. `\h20` representa espacio en la ER y `\h0A`, LF. `--file` preserva los bytes, incluido un salto de línea final; el patrón debe contemplarlo.

**¿Qué significa ASCII en el programa?** El universo consta de los 128 códigos 0 a 127. El comodín y el complemento incluyen controles. La letra `ε` es notación de la ER, no un carácter de entrada ASCII.

**¿Se usó una librería de regex?** No para el parser, Thompson, subconjuntos, simulación ni tokenización. Las estructuras son de la biblioteca estándar. Las fuentes teóricas y la asistencia utilizada se declaran en `FUENTES.md`.

**¿Cuál es la complejidad?** Thompson genera un número de estados lineal en la expresión expandida. La determinización puede ser exponencial en el peor caso. La simulación del AFD realiza una consulta de tabla por carácter y es lineal en la longitud de entrada; el recorrido almacenado también ocupa memoria lineal. El tokenizador de varias reglas no tiene esa misma garantía global: puede explorar prefijos largos repetidamente antes de decidir cada token.

**¿Qué ocurre con expresiones enormes?** Se aplican límites explícitos: longitud de ER 4096, anidamiento 100, AFND 20000 y AFD 4096 por defecto. El límite del AFD se configura con `--max-states`. Si se supera, se informa error 2 y no se inventa un resultado.

**¿Cómo se resuelve la prioridad de tokens?** Primero gana mayor longitud. Si dos reglas consumen exactamente lo mismo, gana la primera del JSON. Las reglas anulables se rechazan para impedir ciclos sin avance.

**¿Por qué una aceptación retorna 1?** Es una exigencia expresa del enunciado, aunque difiere de la convención habitual de éxito Unix. `make run` maneja esa semántica y conserva los errores.

**¿Se minimizó el AFD?** No. Se mantiene visible la correspondencia de subconjuntos para fines de explicación y comprobación; la minimización no es un requisito.

**¿Dónde está la entrega?** En [Medec92227/er-afd](https://github.com/Medec92227/er-afd): fuentes, Makefile, pruebas, tres PDF y evidencia real. La documentación incluye a ambos integrantes. La defensa debe ensayarse con esta versión y el estado del workflow se comprueba en Actions.
