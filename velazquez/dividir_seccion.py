#!/usr/bin/env python3
"""Divide un PDF de sección (generado por dividir_velazquez.py) en capítulos.

Uso (necesita dividir_velazquez.py en la misma carpeta):
    pip install pypdf
    python dividir_seccion.py Seccion_10_X_Quimioterapia_antiinfecciosa_y_antitumoral.pdf
    python dividir_seccion.py mi_archivo.pdf --seccion X --salida capitulos_X

La sección se deduce del nombre del archivo (p. ej. "Seccion_10_X_..."); si lo
has renombrado, indícala con --seccion.
"""

import argparse
import re
import sys
from pathlib import Path

from pypdf import PdfReader

from dividir_velazquez import INDICE, guardar, slug


def detectar_seccion(nombre):
    m = re.search(r"Seccion_\d+_([IVX]+)_", nombre)
    return m.group(1) if m else None


def main():
    parser = argparse.ArgumentParser(description="Divide un PDF de sección del Velázquez en capítulos.")
    parser.add_argument("pdf", help="PDF de una sección")
    parser.add_argument("--seccion", help="Número romano de la sección (II, III, ..., XI)")
    parser.add_argument("--salida", help="Carpeta de salida (por defecto, Capitulos_<sección>)")
    args = parser.parse_args()

    seccion = (args.seccion or detectar_seccion(Path(args.pdf).name) or "").upper()
    secciones = {sec: (i, caps) for i, (sec, _, caps) in enumerate(INDICE)}
    if seccion not in secciones:
        sys.exit("No sé qué sección es. Indícala con --seccion (por ejemplo --seccion X).")
    i, caps = secciones[seccion]
    if len(caps) < 2:
        sys.exit(f"La sección {seccion} no tiene capítulos separados en el índice.")

    reader = PdfReader(args.pdf)
    total = len(reader.pages)
    primera = caps[0][2]
    if i + 1 < len(INDICE):
        esperadas = INDICE[i + 1][2][0][2] - primera
        if total != esperadas:
            print(f"Aviso: el PDF tiene {total} páginas y la sección debería tener {esperadas}. "
                  "Revisa que los cortes caigan bien.")

    carpeta = Path(args.salida or f"Capitulos_{seccion}")
    carpeta.mkdir(parents=True, exist_ok=True)
    print(f"Sección {seccion}: {total} páginas, {len(caps)} capítulos")

    for j, (num, titulo, pag) in enumerate(caps):
        inicio = pag - primera
        fin = caps[j + 1][2] - primera if j + 1 < len(caps) else total
        if inicio >= total:
            print(f"  ! Capítulo {num}: empieza fuera del PDF, se omite")
            continue
        guardar(reader, carpeta / f"Cap_{num:02d}_{slug(titulo)}.pdf", inicio, min(fin, total))

    print(f"Listo. Archivos en: {carpeta.resolve()}")


if __name__ == "__main__":
    main()
