# Auditoría de la implementación ER-AFD

Se revisaron los fuentes de `er_afd/` y su ruta real de ejecución. La comprobación estática se complementa con las pruebas de Ubuntu y la batería adicional reproducible en `tests/additional_validation.py`.

## Reconocimiento sin motores de expresiones regulares

Los módulos del programa no importan `re`, `regex` ni `fnmatch` y no usan `eval`, `exec` o `__import__`. Se inspeccionaron los imports y llamadas mediante el AST de Python, además de leer las funciones que construyen y recorren los autómatas. Las dependencias externas del paquete pertenecen a la biblioteca estándar.

`compile_regex` es una función propia; no es un alias de un motor regex:

```python
def compile_regex(pattern: str, max_dfa_states: int = 4096) -> CompiledRegex:
    parsed = parse_regex(pattern)
    nfa = thompson(parsed)
    return CompiledRegex(pattern, nfa, determinize(nfa, max_dfa_states))
```

Se encuentra al final de `er_afd/automata.py`. La CLI llama a esta función y después a `compiled.match(text)` en `er_afd/cli.py`.

## Construcción automática

| Etapa | Funciones y evidencia verificable |
| --- | --- |
| Analizar la ER | `Parser.parse`, `union`, `concat`, `repeat` y `atom` en `parser.py` construyen el AST. `escape` y `character_class` interpretan escapes y conjuntos. |
| Construir el AFND | `thompson` en `automata.py` recorre el AST. `state()` asigna estados y `edge()` agrega aristas para cada literal, concatenación, unión o cerradura. |
| Determinizar | `determinize` calcula el cierre inicial, procesa subconjuntos alcanzables con una cola y asigna `transitions[(source, label)]` a partir de los movimientos y sus cierres. |
| Reconocer | `DFA.step` obtiene el destino de `self.transitions[(state, self.char_classes[char])]`. `match` y `accepts` recorren esa matriz, carácter por carácter. |
| Tokenizar | `compile_rules` compila cada ER una vez. `tokenize` avanza los AFD con `dfa.step`, conserva la aceptación más larga y aplica el orden de prioridad. |

No hay tablas de reconocimiento precargadas para las expresiones de ejemplo. Los diagramas de los documentos representan resultados del programa; no intervienen en su ejecución. La renumeración coloca los estados iniciales en q0 y Q0.

## Comprobación reproducible

Desde la raíz del proyecto, dentro de Ubuntu de 64 bits y con un usuario normal:

```bash
python3 -m tests.additional_validation --output "$HOME/erafd-adicionales-$(date -u +%Y%m%dT%H%M%SZ).json"
```

El JSON conserva imports, SHA-256 de los módulos revisados y tamaños de autómatas generados para expresiones distintas. También registra los resultados de lenguaje, errores y procesos de CLI. Comprueba por SHA-256, antes y después, que las métricas históricas no cambien.

La revisión del código confirma esta estructura explícita y la ausencia de los motores indicados en el reconocimiento. Los resultados de una muestra finita no demuestran que todas las expresiones y entradas posibles estén libres de errores.
