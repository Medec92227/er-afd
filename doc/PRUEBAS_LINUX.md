# Pruebas locales en Ubuntu y reproducción

Estado al 2 de noviembre de 2026: **pruebas reales en Ubuntu completadas correctamente**: 39 unitarias, 1499 casos con oráculo, 20306 comparaciones AFND/AFD y 16 comprobaciones del verificador, sin fallos. Hay seis capturas reales y registros en [la carpeta de evidencia](evidencias/linux/20261102T180611Z/LEEME_EVIDENCIAS.md). Para repetirlas, consulta [PASOS_PRUEBAS_UBUNTU.md](PASOS_PRUEBAS_UBUNTU.md). Las métricas existentes de `doc/evidencias/metricas.json` conservan su entorno Windows original.

## Entorno elegido

Se utilizó Ubuntu Desktop 26.04.1 LTS de 64 bits, con interfaz gráfica, dentro de VirtualBox 7.2.22 para Windows. La edición Desktop permite trabajar con el escritorio y la terminal de Ubuntu.

Los archivos de instalación se descargaron en las rutas solicitadas:

| Archivo | Ubicación en Windows |
| --- | --- |
| Ubuntu Desktop | `C:\Users\CM_PC\OneDrive\Documents\Programacion\isos\ubuntu-26.04.1-desktop-amd64.iso` |
| VirtualBox | `C:\Users\CM_PC\OneDrive\Documents\Programacion\virtualbox\VirtualBox-7.2.22-175245-Win.exe` |

Antes de ejecutarlos se debe confirmar que su SHA-256 coincide con el manifiesto oficial. El instalador de VirtualBox debe mostrar además una firma digital válida de Oracle. No se necesita el Extension Pack para este proyecto.

## Preparar la máquina virtual

La computadora anfitriona tiene aproximadamente 15.71 GiB de RAM y espacio suficiente en C:. En la inspección del 2 de noviembre había solo 2.03 GiB de RAM libre: cerrar aplicaciones de trabajo y comprobar la memoria disponible antes de encender la VM. Reservar memoria suficiente también para Windows.

Windows reportó `HypervisorPresent=True`. Por eso, los campos de virtualización que aparecen como falsos en consultas del procesador **no demuestran que Intel VT-x esté desactivado en el firmware**. Comprobar el funcionamiento de VirtualBox sin desactivar el hipervisor, la seguridad de Windows ni protecciones del equipo. Si el instalador o VirtualBox solicita reiniciar, guardar el trabajo y realizar el reinicio de forma deliberada.

Configuración inicial de la VM:

| Parámetro | Valor inicial |
| --- | --- |
| Nombre | `Ubuntu-ER-AFD` |
| Tipo | Linux / Ubuntu de 64 bits |
| Memoria | 6144 MB, solo después de liberar RAM suficiente |
| Procesadores | 4 vCPU |
| Disco | VDI dinámico de 40 GB |
| Red | NAT, sin redirección de puertos |
| Medio de arranque | ISO de Ubuntu Desktop indicada arriba |

Instalar Ubuntu **dentro del disco virtual**. No seleccionar ni formatear discos físicos del anfitrión. Crear el usuario de Ubuntu mediante el instalador y escribir sus credenciales directamente en la VM. No añadir contraseñas al repositorio, a los registros ni a las capturas de prueba.

## Pasar el proyecto a Ubuntu

Para la primera ejecución local se copió el proyecto dentro del directorio personal del usuario. Para reproducirla, clonar [Medec92227/er-afd](https://github.com/Medec92227/er-afd) o extraer `ER-AFD_proyecto_completo.zip` en `~/er-afd`. Las pruebas se ejecutan sobre esa copia en el disco de Ubuntu.

En la terminal de Ubuntu:

```bash
# Comprobar que el proyecto esté copiado o extraído en ~/er-afd antes de continuar.
cd ~/er-afd
uname -m
getconf LONG_BIT
python3 --version
make --version
```

Se espera Linux de 64 bits, Python 3.10 o posterior y GNU Make. Si las herramientas no están instaladas, su preparación en Ubuntu puede requerir privilegios de administración:

```bash
sudo apt update
sudo apt install python3 make unzip
```

Ese permiso corresponde a instalar herramientas del sistema. **La configuración, construcción y ejecución de ER-AFD deben realizarse como usuario regular, sin `sudo`.** El programa no necesita paquetes pip ni descargar dependencias para funcionar.

## Ejecutar la comprobación y guardar evidencias

Desde la raíz del proyecto:

```bash
bash tools/verify_linux.sh
```

El script solo funciona en Linux de 64 bits, comprueba que el usuario no sea root y crea una carpeta nueva con fecha UTC en `doc/evidencias/linux/`. Cada ejecución usa su propia carpeta y no sobrescribe la anterior. También se puede indicar una ubicación nueva explícita:

```bash
bash tools/verify_linux.sh "$HOME/evidencias-er-afd-primera-prueba"
```

Esta comprobación incluye:

1. Identificación de Ubuntu, arquitectura, Python, Make y usuario de ejecución.
2. `make config`, `make build` y `make test`.
3. `make run ER='(a|b)*abb' CADENA='aabb'`.
4. Retornos reales de `er-afd`: 1 para aceptación, 0 para rechazo y 2 para error de sintaxis.
5. Cadena vacía con `ε`, JSON válido, exportación de ambos DOT y lectura exacta de un archivo ASCII.
6. Tokenización del ejemplo con varias reglas mediante `er-lex`.
7. Regeneración de métricas con `tests.run_validation` dentro de Linux.
8. `make clean`, comprobación de conservación del código/PDF/evidencia y reconstrucción posterior.

El código **1 de `er-afd` es una aceptación**. El script lo captura de forma explícita para que el shell no lo confunda con una ejecución fallida. El propio verificador devuelve 0 solo cuando todas sus comprobaciones terminan correctamente; devuelve un código no cero y conserva el registro si alguna falla.

Los resultados de referencia actuales son 39 métodos de unittest, 1499 casos con oráculo y 20306 comparaciones AFND/AFD. El verificador imprime las cifras realmente observadas. Si se incorporan nuevos casos, actualizar los documentos con las cifras nuevas; no modificar los resultados históricos de Windows para presentarlos como resultados de Ubuntu.

## Capturas auténticas

Las capturas deben tomarse durante la ejecución real en Ubuntu. Los registros de texto que genera el script son evidencia reproducible, pero no sustituyen las capturas de pantalla solicitadas en el enunciado.

Guardar, como mínimo, imágenes legibles de:

| Captura | Qué debe poder comprobarse |
| --- | --- |
| Entorno | Escritorio o terminal de Ubuntu, `/etc/os-release`, arquitectura de 64 bits y versión de Python. |
| Suite de pruebas | El comando `make test`, número de pruebas y resultado final. |
| Aceptación | Tablas o recorrido de `(a|b)*abb` frente a `aabb`, texto final y retorno 1. |
| Rechazo y error | Un rechazo con retorno 0 y un error de sintaxis con retorno 2. |
| Construcción y limpieza | Ejecución de los objetivos Make y reconstrucción después de limpiar. |

Para volver a mostrar casos individuales en la terminal y capturar el retorno sin que la aceptación detenga una sesión con `set -e`, usar una construcción condicional:

```bash
if python3 dist/er-afd '(a|b)*abb' 'aabb'; then estado=0; else estado=$?; fi
printf 'Código de retorno: %s\n' "$estado"

if python3 dist/er-afd '(a|b)*abb' 'aab'; then estado=0; else estado=$?; fi
printf 'Código de retorno: %s\n' "$estado"

if python3 dist/er-afd '[z-a]' 'a'; then estado=0; else estado=$?; fi
printf 'Código de retorno: %s\n' "$estado"
```

Usar la herramienta de capturas del escritorio de Ubuntu. Conservar los archivos originales dentro de la carpeta de evidencias de la ejecución, con nombres que identifiquen su contenido. Evitar incluir contraseñas, correos privados u otros datos ajenos a las pruebas. No recrear manualmente una salida para hacerla pasar por una captura de Ubuntu.

## Criterio para cerrar esta etapa

La comprobación queda cerrada cuando existe `resultado.json` con `completed: true`, se revisaron los registros y las capturas reales son legibles. Confirmar que `metricas_linux.json` registra una plataforma Linux y que no hay fallos, errores ni diferencias inesperadas.

Estado de la entrega:

1. Los tres PDF reflejan las métricas; casos de prueba incluye las seis capturas reales en las páginas 6 a 11.
2. El README conserva las cifras originales y presenta por separado los 800 casos adicionales.
3. El repositorio reúne código, Makefile, pruebas, tres PDF y evidencias.
4. El estado del workflow de Ubuntu se consulta por separado en GitHub Actions.
5. La defensa de diez minutos debe ensayarse con esta versión final del programa.

La prueba de una muestra finita, aunque no tenga fallos, no garantiza una calificación de 100 puntos. La evaluación final corresponde al docente.

## Fuentes de las versiones y requisitos

- Ubuntu Desktop y sus requisitos: <https://ubuntu.com/download/desktop>
- Manifiesto SHA-256 de Ubuntu 26.04.1: <https://releases.ubuntu.com/26.04.1/SHA256SUMS>
- Versión estable publicada de VirtualBox: <https://download.virtualbox.org/virtualbox/LATEST.TXT>
- Descargas oficiales de Oracle: <https://www.oracle.com/virtualization/technologies/vm/downloads/virtualbox-downloads.html>
- Manifiesto SHA-256 de VirtualBox 7.2.22: <https://download.virtualbox.org/virtualbox/7.2.22/SHA256SUMS>

Versiones verificadas para esta preparación el 2 de noviembre de 2026. Las descargas y su verificación se registran por separado; este documento no sustituye ese comprobante.
