# Pruebas adicionales y revisión del código

La batería nueva terminó correctamente en Ubuntu de 64 bits con Python 3.14.4 y usuario regular. Está separada del histórico **39 pruebas unitarias / 1499 casos / 20306 comparaciones**, que no se sobrescribió.

| Comprobación adicional | Resultado |
| --- | --- |
| Lenguaje, AFND, AFD y simulación | 800 de 800 pares ER/entrada correctos |
| Clasificación | TP 222, TN 578, FP 0, FN 0 |
| Patrones inválidos nuevos | 9 detectados |
| Procesos CLI y JSON | 25 con el retorno esperado |
| Descubrimiento de unittest original | Se conservan 39 pruebas |
| Integridad del histórico | SHA-256 iguales antes y después |

Los nueve patrones inválidos también se prueban desde la CLI; no son nueve procesos adicionales a los 25. Los 800 casos no reproducen ninguna pareja ER/entrada de tests/cases.py.

## Cobertura nueva

- Controles ASCII, su complemento y la diferencia entre lenguaje vacío y épsilon: cuatro patrones por 130 entradas, 520 casos.
- Un conjunto negativo compuesto sobre todas las cadenas de longitud 0 a 3 de un alfabeto de seis caracteres: 259 casos.
- Veintiún casos dirigidos: complementos con macros, diagonales, símbolos literales, posiciones negativas, códigos como GT-007 y NUL con épsilon.
- Errores de hexadecimal/rango/macros/Unicode y límite de estados; los procesos deben retornar 2 y emitir JSON de error sin traceback.
- Archivos escritos en bytes para comprobar NUL, TAB, CR, LF, DEL y bytes fuera de ASCII. No se normalizan CR/LF.
- Argumentos que comienzan con guion, usando --, y diferencia entre la letra t escapada y un tabulador real.

Los oráculos usan igualdad, longitud y pertenencia numérica a ASCII. No se usa otro motor regex para determinar las respuestas esperadas. El resultado describe esta muestra finita, no todas las entradas posibles.

## Repetir en Ubuntu

Desde la raíz del proyecto:

```bash
python3 -m tests.additional_validation --output "$HOME/erafd-adicionales-$(date -u +%Y%m%dT%H%M%SZ).json"
```

La salida debe indicar **passed: true**. completed: true por sí solo solo indica que el ejecutor terminó. El destino debe ser nuevo y no se ejecuta con sudo. Este módulo no usa el nombre test*.py, por lo que no cambia el descubrimiento de las 39 pruebas originales.

## Código y resultados

- Ejecutor: [tests/additional_validation.py](../tests/additional_validation.py).
- Auditoría del reconocimiento: [AUDITORIA_IMPLEMENTACION.md](AUDITORIA_IMPLEMENTACION.md).
- Resultado completo: [doc/evidencias/linux/adicionales_20261103T033444Z/resultado_adicional.json](../doc/evidencias/linux/adicionales_20261103T033444Z/resultado_adicional.json).
- La misma carpeta conserva el registro de ejecución, identificación SHA-256 del ejecutor y manifiesto de evidencias.

Las fuentes de er_afd/ no necesitaron cambios para superar esta batería. La documentación distingue la ejecución local de Ubuntu de las ejecuciones de GitHub Actions, cuyo estado y registros se consultan en el repositorio.
