# Repetir las pruebas de ER-AFD en Ubuntu

La ejecución del 2 de noviembre de 2026 terminó correctamente en Ubuntu Desktop 26.04.1 LTS, de 64 bits, con Python 3.14.4 y GNU Make 4.4.1. Se comprobaron 39 pruebas unitarias, 1,499 casos con resultado esperado y 20,306 comparaciones entre AFND y AFD, sin fallos. Las 16 comprobaciones del verificador pasaron. También funcionaron el ejecutable Unix directo y el espacio escapado en Bash.

## 1. Entrar y abrir la terminal

Abre VirtualBox, inicia **Ubuntu-ER-AFD** y entra con el usuario **erafd** y la contraseña que elegiste. Haz clic dentro de Ubuntu y pulsa **Ctrl + Alt + T**. Si necesitas devolver el teclado o el ratón a Windows, pulsa **Ctrl derecho**.

En la terminal escribe:

```bash
cd ~/er-afd
```

## 2. Ejecutar la comprobación completa

```bash
bash tools/verify_linux.sh
```

No uses `sudo`: el proyecto se prueba con tu usuario normal y no necesita descargar paquetes. El script configura, construye, prueba, valida JSON/DOT/archivos/lexer, limpia y reconstruye. Al terminar correctamente imprime **VERIFICACION LINUX COMPLETADA** y la carpeta que contiene la evidencia.

Cada repetición crea una carpeta nueva en `doc/evidencias/linux/` y conserva las anteriores. Para localizar la última:

```bash
ls -td doc/evidencias/linux/*/ | head -n 1
```

En esa carpeta revisa `resultado.json`: debe decir `"completed": true`, cero fallos y cero errores. `transcripcion.log` contiene la ejecución completa; `retornos.tsv` compara los retornos observados con los esperados y `metricas_linux.json` guarda las métricas de esa ejecución.

Si aparece **Verificación incompleta**, conserva esa carpeta y lee el último error de `transcripcion.log`. No presentes esa ejecución como aprobada.

## 3. Probar casos individuales

Primero deja construido el programa:

```bash
make config
make build
```

Ejecuta cada pareja de líneas junta. La segunda línea consulta inmediatamente el retorno del programa anterior.

**Aceptación y tablas completas pequeñas:**

```bash
./dist/er-afd 'a' 'a'
echo "Retorno: $?"
```

Debe mostrar AFND, AFD, recorrido, **Cadena aceptada** y retorno **1**.

**Expresión con unión y repetición:**

```bash
./dist/er-afd '(a|b)*abb' 'aabb'
echo "Retorno: $?"
```

Debe aceptar con retorno **1**.

**Rechazo:**

```bash
./dist/er-afd 'a' 'b'
echo "Retorno: $?"
```

Debe mostrar **Cadena rechazada** y retorno **0**.

**Error de sintaxis:**

```bash
./dist/er-afd '[z-a]' 'a'
echo "Retorno: $?"
```

Debe diagnosticar el rango invertido y devolver **2**.

**Cadena vacía y espacio escapado:**

```bash
./dist/er-afd 'ε' '' --json
echo "Retorno: $?"
./dist/er-afd 'hola\ mundo' 'hola mundo' --json
echo "Retorno: $?"
```

Ambos casos deben aceptar con retorno **1**. Conserva las comillas simples y la diagonal del ejemplo para que Bash entregue correctamente la expresión al programa.

La convención del programa es **1 = aceptación, 0 = rechazo y 2 = error**. El verificador completo, Make y el lexer usan **0 cuando terminan correctamente**; son interfaces diferentes.

## 4. Suite y tokenización por separado

```bash
make test
./dist/er-lex --rules examples/reglas.json --file examples/programa.txt
```

`make test` debe terminar con `Ran 39 tests` y `OK`. El ejemplo del lexer devuelve siete tokens: SI, IDENTIFICADOR, IGUAL, NUMERO, SUMA, IDENTIFICADOR y PUNTO_COMA.

## 5. Limpiar y volver a construir

```bash
make clean
make build
./dist/er-afd 'a*b' 'aaab'
echo "Retorno: $?"
```

La limpieza conserva los fuentes, documentos y evidencias. El último caso debe aceptar con retorno **1**.

## 6. Tomar tus propias capturas

Deja visible el comando y su resultado en la terminal de Ubuntu. Maximiza la terminal y asegúrate de que el texto se lea. Dentro de Ubuntu, **ImprPant / Print Screen** abre la herramienta de captura; elige pantalla o ventana y pulsa el botón de captura. Encontrarás la imagen en **Imágenes**, dentro de la carpeta de capturas. La [ayuda oficial de GNOME](https://help.gnome.org/gnome-help/screen-shot-record.html) explica los controles.

Conserva las imágenes originales como PNG y cópialas a la carpeta de evidencias de tu ejecución. Puedes nombrarlas `01_entorno.png`, `02_pruebas.png`, `03_aceptacion.png`, `04_rechazo_error.png`, `05_lexer.png` y `06_limpieza.png`. Muestra las salidas reales y evita incluir contraseñas en la pantalla.

## Evidencia ya guardada

La ejecución completa y sus seis capturas están en:

```text
~/er-afd/doc/evidencias/linux/20261102T180611Z/
```

En Windows hay una copia en la carpeta del proyecto dentro de `outputs/er-afd/doc/evidencias/linux/20261102T180611Z/` y un ZIP independiente llamado **Evidencias_Ubuntu_ER-AFD.zip**. La evidencia original de Windows se mantiene separada.
