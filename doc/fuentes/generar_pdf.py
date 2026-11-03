"""Genera los PDF de doc/ a partir de estos HTML usando Chrome, Chromium o Edge.

Uso: python3 doc/fuentes/generar_pdf.py
"""
from pathlib import Path
import shutil
import subprocess
import sys

AQUI = Path(__file__).resolve().parent
DOCUMENTOS = {
    "reporte.html": ("Reporte técnico", "Reporte_tecnico.pdf"),
    "casos.html": ("Casos de prueba", "Casos_de_prueba.pdf"),
    "manual.html": ("Manual de usuario", "Manual_usuario.pdf"),
}
NAVEGADORES = [
    "chromium", "chromium-browser", "google-chrome", "msedge",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]


def navegador() -> str:
    for nombre in NAVEGADORES:
        ruta = shutil.which(nombre) or (nombre if Path(nombre).is_file() else None)
        if ruta:
            return ruta
    sys.exit("No se encontró Chrome, Chromium ni Edge.")


def main() -> None:
    exe = navegador()
    portada = (AQUI / "portada.html").read_text(encoding="utf-8")
    for fuente, (titulo, salida) in DOCUMENTOS.items():
        html = (AQUI / fuente).read_text(encoding="utf-8")
        html = html.replace("{{PORTADA:" + titulo + "}}", portada.replace("{{DOCUMENTO}}", titulo))
        # El nombre del documento va en el encabezado de cada página.
        html = html.replace("</head>", "<style>@page { @top-right { content: \"" + titulo + "\"; } } @page :first { @top-right { content: none; } }</style></head>")
        temporal = AQUI / ("_" + fuente)
        temporal.write_text(html, encoding="utf-8")
        destino = AQUI.parent / salida
        subprocess.run([exe, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={destino}", temporal.as_uri()],
                       check=True, capture_output=True)
        temporal.unlink()
        print("Generado:", destino.name)


if __name__ == "__main__":
    main()
