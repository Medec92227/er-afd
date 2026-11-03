# Referencia de la consola

[Volver a la presentación del proyecto](../README.md). Los comandos se ejecutan desde la raíz del repositorio.

## Uso de er-afd

```text
er-afd <ER> <cadena>
er-afd <ER> --file <archivo>
```

Por defecto muestra:

1. El AFND: estados `q0`, `q1`, etc.; alfabeto, estado inicial `q0`, estados finales y transiciones.
2. El AFD: estados `Q0`, `Q1`, etc.; alfabeto, estado inicial `Q0`, estados finales y transiciones.
3. El recorrido de la cadena, con líneas de la forma `Q0|a|Q1`.
4. `Cadena aceptada` o `Cadena rechazada`.

Los códigos de salida forman parte de la interfaz:

| Código | Significado |
| --- | --- |
| 1 | Cadena aceptada por el AFD. |
| 0 | Cadena válida como entrada, pero rechazada por el AFD. |
| 2 | Sintaxis inválida, entrada fuera de ASCII, error de archivo o límite de recursos. |

Opciones adicionales:

| Opción | Uso |
| --- | --- |
| `--file PATH` | Lee bytes ASCII de un archivo en lugar de recibir el segundo argumento. Conserva los saltos de línea. |
| `--json` | Emite una representación JSON en lugar de la presentación textual. Mantiene los mismos códigos de salida. |
| `--dot PREFIX` | Exporta `PREFIX.afnd.dot` y `PREFIX.afd.dot` para visualizar los autómatas. |
| `--max-states N` | Limita los estados construidos del AFD; por defecto 4096. |
| `--help` | Muestra la ayuda de uso. |

```sh
er-afd '(a|b)*abb' 'aabb' --json
er-afd 'a*b' 'aaab' --dot automata
er-afd '(a|b)*abb\h0A' --file examples/cadena.txt
```

El archivo `examples/cadena.txt` incluye un LF final. En reconocimiento completo ese LF cuenta como carácter; `\h0A` lo reconoce. Para producir una entrada sin salto final, puede utilizarse `printf 'aabb' > cadena.txt` y luego `er-afd '(a|b)*abb' --file cadena.txt`.

Los archivos DOT son opcionales y no se requiere Graphviz para ejecutar el programa. Si ya se dispone de Graphviz, `dot -Tpng automata.afd.dot -o automata.afd.png` produce una imagen.

## Sintaxis de expresiones regulares

La prioridad de mayor a menor es: agrupación/átomos, cerradura `*`, concatenación implícita y unión `|`.

| Sintaxis | Significado | Ejemplo |
| --- | --- | --- |
| `ab` | Concatenación. | Reconoce `ab`. |
| `a\|b` | Unión. | Reconoce `a` o `b`. |
| `r*` | Cero o más repeticiones de `r`. | `a*` acepta vacío, `a`, `aa`... |
| `(r)` | Agrupación con precedencia. | `(ab)*` |
| `.` | Cualquier carácter ASCII, incluidos controles. | `a.b` |
| `ε` | Cadena vacía; no consume entrada. | `aεb` reconoce `ab`. |
| `[abc]` | Cualquiera de los caracteres del conjunto. | `[abc]*` |
| `[^abc]` | Cualquier carácter ASCII excepto los indicados. | `[^0-9]` |
| `[a-z]` | Rango inclusivo dentro de un conjunto. | `[a-zA-Z]` |
| `\*`, `\(`, `\\` | Escape de un carácter literal. | `\*` reconoce `*`; `\\` reconoce una diagonal invertida. |
| `\p` | Escape genérico: el carácter siguiente, salvo secuencias especiales. | Reconoce `p`. |
| `\N` | Un dígito. | Equivale a `[0-9]`. |
| `\A` | Una letra mayúscula. | Equivale a `[A-Z]`. |
| `\a` | Una letra minúscula. | Equivale a `[a-z]`. |
| `\z` | Una letra mayúscula o minúscula. | Equivale a `[a-zA-Z]`. |
| `\hXX` | Un carácter ASCII mediante exactamente dos dígitos hexadecimales. | `\h20`: espacio; `\h41`: `A`; `\h0A`: LF. |

La unión se escribe `a|b`; el patrón `a\|b` reconoce literalmente `a|b`.

No se implementan las extensiones de otros motores como `+`, `?`, `{m,n}`, anclas, grupos capturadores ni referencias hacia atrás. Para una o más repeticiones se escribe `rr*`, por ejemplo `\N\N*`. `\n` y `\t` son escapes genéricos y representan `n` y `t`; para LF y tabulador se usan `\h0A` y `\h09`.

La entrada pertenece a ASCII completo, códigos 0 a 127. El símbolo `ε` se permite como notación del patrón; no es un carácter ASCII de entrada. Los controles pueden probarse mediante archivos o la API Python, ya que una terminal no permite transmitir NUL como argumento de un proceso. `\h80` a `\hFF` y texto con letras acentuadas se rechazan como errores de entrada.

Las expresiones y las ramas vacías no son atajos de épsilon: utiliza `ε` de forma explícita. Por ejemplo, `a|` es inválida y `a|ε` representa una alternativa vacía. El parser informa errores de paréntesis, conjuntos, rangos y escapes incompletos.

## Espacios y comillas

En Linux, usa comillas simples ASCII para que el shell preserve las diagonales y los operadores. También son válidas las comillas dobles, con las reglas de escape propias del shell. No uses comillas tipográficas.

```sh
er-afd 'hola mundo' 'hola mundo'
er-afd 'hola\ mundo' 'hola mundo'
er-afd 'hola\h20mundo' 'hola mundo'
er-afd hola\ mundo hola\ mundo
```

El shell resuelve la diagonal que protege un espacio cuando está fuera de comillas. El programa no vuelve a interpretar escapes de la cadena: en `er-afd 'a\*' 'a*'`, solo el primer argumento es una ER; el segundo es texto literal.

## Alfabeto y determinismo

Las etiquetas de la ER se conservan en orden de primera presentación. El AFND muestra épsilon en su posición si aparece explícitamente y lo agrega al final si solo surge de Thompson. El AFD elimina las transiciones épsilon.

Los predicados de clases y comodines pueden solaparse, como en `a|.`. La conversión considera qué transiciones coinciden con cada carácter ASCII y construye los subconjuntos correspondientes. Una etiqueta de la expresión no se usa como una prioridad para ignorar otra transición coincidente. Así se conserva un destino determinista por estado y carácter.

La salida conserva `Σ` como alfabeto de origen y presenta `Γ` como particiones disjuntas utilizadas en la matriz del AFD, con una leyenda de los caracteres de cada clase. Las clases `C0`, `C1`, etc., incluyen los caracteres residuales cuando corresponda. También muestra qué subconjunto de estados del AFND representa cada estado del AFD.

El programa no aplica minimización de estados: el objetivo es hacer visible Thompson y la construcción de subconjuntos. Un estado pozo representa recorridos sin posibilidad de aceptación y se crea si es alcanzable. Todo estado utilizado en las transiciones debe estar declarado en el conjunto de estados.

Los límites preventivos son 4096 caracteres por ER, 100 niveles de paréntesis, 20000 estados de AFND y 4096 estados de AFD por defecto. El límite del AFD se ajusta con `--max-states`. Superar un límite produce error explícito; no se emite una aceptación o rechazo supuesto.

## Tokenización con varias reglas

La extensión `er-lex` cubre el uso de un conjunto de ER para analizar un texto o archivo fuente:

```sh
python3 dist/er-lex --rules examples/reglas.json --file examples/programa.txt
python3 dist/er-lex --rules examples/reglas.json --text 'if contador = 12 + valor;'
```

También funciona desde fuentes mediante `python3 er-lex ...`. Las reglas se describen como una lista JSON ordenada:

```json
[
  {"name": "ESPACIO", "regex": "[\\h20\\h09\\h0A][\\h20\\h09\\h0A]*", "skip": true},
  {"name": "SI", "regex": "if"},
  {"name": "IDENTIFICADOR", "regex": "(\\z|_)(\\z|\\N|_)*"},
  {"name": "NUMERO", "regex": "\\N\\N*"}
]
```

Se consume la coincidencia de mayor longitud desde la posición actual. En un empate gana la primera regla de la lista. Por ejemplo, `if` se clasifica como `SI` y `ifx` como `IDENTIFICADOR`. `skip: true` consume texto sin emitir tokens. Las reglas que aceptan vacío se rechazan para asegurar que cada paso avance.

La salida es una lista JSON con `type`, `value`, `start`, `end`, `line` y `column`. Los offsets empiezan en 0 y `end` es exclusivo; líneas y columnas empiezan en 1. LF inicia una nueva línea y CR cuenta como carácter ordinario. Un carácter sin regla o un archivo fuera de ASCII produce error con ubicación. `er-lex` retorna **0** al tokenizar correctamente y **2** en error; los códigos 1/0 de aceptación/rechazo corresponden únicamente a `er-afd`.

## Make y construcción

| Objetivo | Efecto |
| --- | --- |
| `make config` | Verifica Python y describe los requisitos; no descarga dependencias. |
| `make build` | Comprueba la sintaxis y crea los zipapps autónomos `dist/er-afd` y `dist/er-lex`. Requieren Python al ejecutarse. |
| `make run` | Construye y ejecuta el ejemplo predeterminado `(a\|b)*abb` con `aabb`. |
| `make test` | Ejecuta la suite de `unittest`. |
| `make clean` | Elimina zipapps, staging de construcción y cachés Python. Conserva fuentes, ejemplos, documentación y evidencias. |

```sh
make run ER='(a|b)*abb' CADENA='aabb'
make run ER='hola\h20mundo' CADENA='hola mundo'
make clean
```

`make run` informa el código semántico del programa y trata tanto aceptación como rechazo como ejecución válida del objetivo. Los errores del programa sí hacen fallar Make. `ER` y `CADENA` se transfieren por variables de entorno al helper y se pasan al proceso como argumentos separados.

Los zipapps incluyen un `__main__.py` que llama a `raise SystemExit(main())`, de modo que conservan los códigos 1/0/2. La construcción utiliza `zipapp`, `compile` y operaciones de archivos de la biblioteca estándar.

Para una ejecución puntual en Windows puede invocarse `python tools/build.py config`, `python tools/build.py build` y `python -m unittest discover -s tests -v`. El producto solicitado es una herramienta de consola para Linux.

