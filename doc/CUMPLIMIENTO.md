# Matriz de cumplimiento del enunciado

Referencia: documento proporcionado por el usuario, «ER-AFD: Convertidor de ER a AFD», René Ornélyz, septiembre de 2026, páginas 3 a 8. Las páginas 1 y 2 corresponden a portada e índice.

Esta tabla distingue la implementación, la publicación en [Medec92227/er-afd](https://github.com/Medec92227/er-afd) y las pruebas locales reales en Windows y Ubuntu de las ejecuciones de CI consultables en GitHub Actions. «Implementado» describe una funcionalidad verificable del código, no una garantía de perfección universal.

| Página | Requisito | Evidencia en el proyecto | Estado |
| --- | --- | --- | --- |
| 3 | Conversión explícita ER a AFND y luego a AFD. | `er_afd/parser.py`; `thompson()` y `determinize()` en `er_afd/automata.py`; `doc/Reporte_tecnico.pdf`. | Implementado y probado localmente. |
| 3 | Mostrar estados, transiciones y finales de ambos autómatas. | `CompiledRegex.format_tables()` / `format_automata()`; `doc/evidencias/04_compleja.txt`. | Implementado. |
| 3 | Evaluar cadenas aceptadas y rechazadas. | `DFA.match()` y `DFA.accepts()`; `tests/test_engine.py`; `tests/test_cli.py`. | Implementado y probado. |
| 3 | Contexto general de conjunto de ER para texto/archivo fuente. | Extensión `er_afd/lexer.py`; `er-lex`; `examples/reglas.json`; `examples/programa.txt`; `tests/test_lexer.py`. | Incluido: varias reglas, máxima longitud, prioridad y `skip`. |
| 3-4 | Concatenación implícita, unión, cerradura de Kleene y paréntesis. | Parser descendente; familias de casos en `tests/cases.py`; precedencia en `doc/Reporte_tecnico.pdf`. | Implementado y probado. |
| 3 | Comodín punto para cualquier símbolo y ε como vacío. | Universo ASCII en `parser.py`; épsilon-cierre en `automata.py`; casos de los 128 códigos. | Implementado; universo ASCII 0..127 documentado. |
| 4 | Conjuntos `[abc]`, complementos y rangos. | `Parser.character_class()`; pruebas de rangos, negativos y solapamientos. | Implementado y probado. |
| 4 | Escape genérico y diagonal invertida literal. | `Parser.escape()`; casos de escape literal y espacios. | Implementado y probado. |
| 4 | Secuencias especiales de dígitos, ASCII hexadecimal, mayúsculas, minúsculas y letras. | `Parser.escape()`; familias `hexadecimal`, `digitos`, `clases-especiales` y validación de ASCII completo. | Implementado y probado. |
| 4 | Thompson y construcción de subconjuntos. | Funciones propias `thompson()` y `determinize()`; explicación y diagramas en `doc/Reporte_tecnico.pdf`. | Implementado; no sustituido por un motor externo. |
| 4 | Formato `estado actual`, símbolo y destino(s), separados por barras verticales. | `format_automata()` y traza en `cli.py`; capturas en `doc/Casos_de_prueba.pdf`. | Implementado; controles y operadores literales se muestran escapados. |
| 4 | Estados `qi` y `Qi`, correlativos desde 0; inicios q0 y Q0. | Renumeración del AFND y BFS de subconjuntos; pruebas estructurales. | Implementado. |
| 4 | Alfabeto en orden de presentación; punto presente si se utiliza. | `Parser.register()` y alfabeto de origen en las tablas. | Implementado; sin duplicados. |
| 4 | ε en el orden explícito o agregado al final para el AFND. | `ParsedRegex.alphabet`; `thompson()`; casos de orden de alfabeto. | Implementado. |
| 4-5 | AFD sin ε y con transiciones deterministas. | Particiones disjuntas Γ y tabla total; `DFA.step()`; comparaciones AFND/AFD. | Implementado; Σ conserva el alfabeto de origen y Γ explica las particiones operativas. |
| 5 | Recorrido paso a paso y texto final exacto. | `er_afd/cli.py`; `doc/evidencias/01_aceptada.txt`, `02_rechazada.txt`. | Implementado. |
| 5 | Retorno 1 aceptada, 0 rechazada. | `cli.main()`; launchers y zipapps con `SystemExit`; pruebas de proceso. | Implementado; errores diferenciados con código 2. |
| 5 | Prohibición de motores de regex para el núcleo. | Parser, Thompson, subconjuntos, simulación y lexer propios con biblioteca estándar. | Cumplido en la implementación. |
| 5 | Atribuir fuentes y evitar copia sin cita. | `FUENTES.md`; referencias del reporte; declaración de asistencia. | Atribución incluida; los autores deben declarar la asistencia según las normas del curso. |
| 6 | Interfaz de consola `er-afd <ER> <cadena>`. | `er-afd`, `er_afd/cli.py`, `dist/er-afd` después de `make build`. | Implementado. |
| 6 | Espacios con escape o comillas; entrada ASCII. | `README.md`, `doc/Manual_usuario.pdf`; ejemplos, validación ASCII y pruebas. | Implementado; el shell interpreta el escape externo y la cadena no reinterpreta escapes de ER. |
| 6 | Linux de 64 bits, Python y usuario regular. | Código portátil de biblioteca estándar; Makefile; zipapps; `.github/workflows/ci.yml`. | Verificado en Ubuntu 26.04.1 LTS x86_64, Python 3.14.4, GNU Make 4.4.1 y UID 1000; sin root. Registros y seis PNG en `doc/evidencias/linux/20261102T180611Z/`. |
| 6 | Código fuente Python en GitHub o GitLab y enlace de entrega. | Repositorio público [Medec92227/er-afd](https://github.com/Medec92227/er-afd), rama `main`, con fuentes, Makefile, tests y doc/. | Fuentes, Makefile, pruebas, PDF y evidencias incluidos en la entrega pública. |
| 6 | `make config`, `make build`, `make run`, `make clean`. | `Makefile` y `tools/build.py`; configuración/construcción de zipapps comprobadas localmente. | Verificados con GNU Make en Ubuntu: configuración, construcción, ejecución, limpieza y reconstrucción; verificador 16/16. |
| 6 | Documentación en PDF dentro de `doc/`. | `Reporte_tecnico.pdf`, `Manual_usuario.pdf`, `Casos_de_prueba.pdf`. | Los tres PDF están incluidos en doc/ y se verificó su integridad. |
| 6 | Reporte de algoritmos. | `doc/Reporte_tecnico.pdf`: parser, Thompson, épsilon-cierre, subconjuntos, particiones y simulación. | Incluido como entregable documental. |
| 6 | Casos de prueba con capturas de ejecución. | `doc/Casos_de_prueba.pdf`; `doc/evidencias/`; textos, imágenes y JSON reproducibles. | Evidencia local incluida y resultados trazables. |
| 6 | Manual de instalación y ejecución. | `doc/Manual_usuario.pdf`; `README.md`. | Incluido como entregable documental. |
| 7 | Conversión 40%, simulación 30%, tablas 15%, documentación/código 15%. | Código y pruebas por módulo, tablas de ambos autómatas y tres PDF. | Los cuatro apartados tienen evidencia; la calificación corresponde al docente. |
| 7 | Métricas de detección. | `doc/evidencias/metricas.json`: 1499/1499 correctos, 710 TP, 789 TN, 0 FP, 0 FN; 20306/20306 comparaciones. | 100% observado en muestra finita; no se extrapola a una precisión universal. |
| 7 | Documentación profesional con diagramas y código limpio con pruebas. | PDFs; separación parser/autómatas/CLI/lexer; 39 pruebas unittest sin fallos en el registro. | Incluido y comprobado localmente. |
| 7 | Funcionalidades adicionales y pruebas completas de la implementación. | JSON, exportación DOT, archivos, límites, lexer multirregla, CI y pruebas de errores. | Extras incluidos; «completo» no implica cobertura de todas las entradas posibles. |
| 7 | Defensa de 10 minutos: demo, diseño, métricas y preguntas. | `doc/DEFENSA.md` con guion 0-2, 2-5, 5-7 y 7-10 minutos. | Guion preparado; exposición a cargo de los autores. |
| 8 | Cronograma tentativo de etapas y entrega. | Imagen del enunciado: investigación/diseño, entrada ER, conversión, análisis, salida; hito 31/10 bajo encabezados de 2026. | Información de planificación; no agrega un módulo de software. Confirmar la fecha oficial con el curso. |

## Interpretaciones registradas

Revisión adicional del código: `AUDITORIA_IMPLEMENTACION.md` identifica el flujo real parser → Thompson → subconjuntos → matriz, sin motores regex en el reconocimiento. `PRUEBAS_ADICIONALES.md` registra 800 casos nuevos de lenguaje, 9 patrones inválidos y 25 procesos CLI ejecutados correctamente en Ubuntu. Las métricas históricas 39/1499/20306 se conservaron por SHA-256 antes y después; los nueve patrones también están dentro de las comprobaciones de CLI.

- El texto general menciona un conjunto de ER, mientras la interfaz obligatoria recibe una. Se preservó la interfaz solicitada y se añadió `er-lex` para el conjunto de reglas.
- El universo ASCII se fijó en los códigos 0..127, incluidos controles; esto define sin ambigüedad el punto y los complementos.
- Las etiquetas solapadas del origen se descomponen en particiones disjuntas, con una leyenda Γ, sin perder el orden de presentación de Σ.
- El ejemplo del PDF utiliza Q3 sin declararlo en su conjunto Q. La implementación declara todos los estados utilizados y agrega el pozo alcanzable en forma coherente.
- La aceptación se comunica con retorno 1 por exigencia explícita, aunque sea distinta de la convención de éxito Unix.
- Las expresiones vacías y las ramas sin operando son errores; la cadena vacía del lenguaje se escribe explícitamente `ε`.

## Entrega y defensa

1. Las portadas universitarias incluyen los dos integrantes y sus carnés, tal como fueron proporcionados.
2. Comprobación Linux completada: 39 unitarias, 1499 casos con oráculo y 20306 comparaciones AFND/AFD sin fallos. La ejecución conserva registros, hashes y seis capturas reales; `PASOS_PRUEBAS_UBUNTU.md` permite repetirla.
3. Los tres PDF universitarios y README reflejan Ubuntu. Casos de prueba incorpora visualmente las seis capturas en su anexo de capturas; las portadas y el formato proporcionados se conservan.
4. Comprobar el árbol completo de [Medec92227/er-afd](https://github.com/Medec92227/er-afd) y el resultado del workflow de Ubuntu, y entregar ese enlace.
5. Ensayar la defensa con el programa y la documentación finales.
