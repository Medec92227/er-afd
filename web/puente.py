"""Conecta la página con el paquete er_afd. Se ejecuta dentro de Pyodide."""
import json

from er_afd import compile_regex
from er_afd.cli import trace_char


def analizar(er: str, cadena: str, max_estados: int = 500) -> str:
    try:
        compilado = compile_regex(er, max_dfa_states=max_estados)
        resultado = compilado.match(cadena)
    except ValueError as error:
        return json.dumps({"codigo": 2, "error": str(error)}, ensure_ascii=False)
    datos = compilado.to_dict()
    recorrido = [[f"Q{p.source}", trace_char(p.symbol), f"Q{p.target}"] for p in resultado.trace]
    # La misma salida que imprime er-afd en la terminal.
    consola = [compilado.format_tables(), ""]
    consola += ["|".join(paso) for paso in recorrido]
    consola.append("Cadena aceptada" if resultado.accepted else "Cadena rechazada")
    return json.dumps({
        "codigo": int(resultado.accepted),
        "aceptada": resultado.accepted,
        "consola": "\n".join(consola),
        "dot_afnd": compilado.to_dot("nfa"),
        "dot_afd": compilado.to_dot("dfa"),
        "recorrido": recorrido,
        "detenido": len(resultado.trace) < len(cadena),
        "estado_final": f"Q{resultado.final_state}",
        "afnd": datos["nfa"],
        "afd": datos["dfa"],
    }, ensure_ascii=False)
