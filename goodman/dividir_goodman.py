#!/usr/bin/env python3
"""Divide el PDF del Goodman & Gilman en un PDF por capítulo.

No necesita el índice: busca los capítulos solo, de dos formas:
  1. Con los marcadores del PDF (el índice lateral del visor), si los tiene.
  2. Si no, leyendo el texto de cada página y buscando "Capítulo N".

Uso:
    pip install pypdf
    python dividir_goodman.py Goodman.pdf
    python dividir_goodman.py Goodman.pdf --listar        # solo muestra lo que encontró
    python dividir_goodman.py Goodman.pdf --por-texto     # ignora los marcadores
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

from pypdf import PdfReader, PdfWriter

CAPITULO = re.compile(r"cap[ií]tulo\s+(\d{1,3})\b", re.IGNORECASE)
# En el texto solo cuenta "Capítulo N" o "CAPÍTULO N" al principio de una línea
# (título o encabezado). Así no confunde frases como "véase el capítulo 7" ni
# una referencia partida en dos renglones ("capítulo 7, la absorción...").
CAPITULO_LINEA = re.compile(r"^\s*(?:Cap[ií]tulo|CAP[IÍ]TULO)\s+(\d{1,3})\b(?!\s*[,;)])", re.MULTILINE)


def slug(texto, largo=60):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^A-Za-z0-9]+", "_", texto).strip("_")
    return texto[:largo].rstrip("_")


def aplanar_marcadores(reader, items=None, nivel=0, salida=None):
    """Devuelve [(nivel, título, índice de página)] de todo el árbol de marcadores."""
    if salida is None:
        salida = []
        items = reader.outline
    for item in items:
        if isinstance(item, list):
            aplanar_marcadores(reader, item, nivel + 1, salida)
            continue
        try:
            pagina = reader.get_destination_page_number(item)
        except Exception:
            continue
        if pagina is not None:
            salida.append((nivel, str(item.title).strip(), pagina))
    return salida


def capitulos_por_marcadores(reader):
    """Elige los marcadores que son capítulos: [(número, título, página)]."""
    try:
        marcadores = aplanar_marcadores(reader)
    except Exception:
        return []
    if not marcadores:
        return []

    # Preferimos los marcadores que dicen "Capítulo N".
    candidatos = []
    for _, titulo, pagina in marcadores:
        m = CAPITULO.search(titulo)
        if m:
            candidatos.append((int(m.group(1)), titulo, pagina))
    if len(candidatos) >= 5:
        return limpiar(candidatos)

    # Si no, marcadores que empiezan por un número ("12. Farmacocinética...").
    candidatos = []
    for _, titulo, pagina in marcadores:
        m = re.match(r"^\s*(\d{1,3})[\s.:\-]+(\D.*)$", titulo)
        if m:
            candidatos.append((int(m.group(1)), titulo, pagina))
    if len(candidatos) >= 5:
        return limpiar(candidatos)
    return []


def capitulos_por_texto(reader, lineas=6):
    """Busca "Capítulo N" al principio de cada página. Un capítulo empieza en la
    primera página donde aparece un número de capítulo mayor que el anterior
    (así los encabezados repetidos en cada página no generan cortes de más)."""
    capitulos = []
    actual = 0
    total = len(reader.pages)
    for i, pagina in enumerate(reader.pages):
        if i % 100 == 0:
            print(f"  leyendo página {i + 1}/{total}...")
        try:
            texto = pagina.extract_text() or ""
        except Exception:
            continue
        cabecera = "\n".join(texto.strip().splitlines()[:lineas])
        encontrados = list(CAPITULO_LINEA.finditer(cabecera))
        if len({e.group(1) for e in encontrados}) != 1:
            continue  # nada, o varios capítulos distintos (página de índice)
        m = encontrados[0]
        num = int(m.group(1))
        if actual < num <= actual + 3:
            titulo = titulo_tras(cabecera, m.end())
            capitulos.append((num, f"Capítulo {num} {titulo}".strip(), i))
            actual = num
    return capitulos


def titulo_tras(texto, posicion):
    resto = texto[posicion:].strip().splitlines()
    for linea in resto:
        linea = linea.strip(" .:-–—")
        if len(linea) > 3 and not linea.isdigit():
            return linea
    return ""


def limpiar(capitulos):
    """Ordena por página, quita repetidos y números que retroceden."""
    capitulos.sort(key=lambda c: c[2])
    salida, vistos = [], set()
    for num, titulo, pagina in capitulos:
        if num in vistos or (salida and pagina <= salida[-1][2]):
            continue
        vistos.add(num)
        salida.append((num, titulo, pagina))
    return salida


def guardar(reader, ruta, inicio, fin):
    """Guarda las páginas [inicio, fin) (índices base 0) en ruta."""
    writer = PdfWriter()
    for idx in range(inicio, fin):
        writer.add_page(reader.pages[idx])
    with open(ruta, "wb") as f:
        writer.write(f)
    tam = ruta.stat().st_size / 1e6
    print(f"  {ruta.name}: páginas {inicio + 1}-{fin} ({fin - inicio} págs., {tam:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Divide el Goodman en capítulos.")
    parser.add_argument("pdf", help="Ruta al PDF del Goodman")
    parser.add_argument("--salida", default="goodman_capitulos", help="Carpeta de salida")
    parser.add_argument("--listar", action="store_true", help="Solo muestra los capítulos encontrados")
    parser.add_argument("--por-texto", action="store_true", help="No usar los marcadores del PDF")
    args = parser.parse_args()

    reader = PdfReader(args.pdf)
    total = len(reader.pages)
    print(f"PDF con {total} páginas")

    capitulos = [] if args.por_texto else capitulos_por_marcadores(reader)
    if capitulos:
        print(f"Encontré {len(capitulos)} capítulos en los marcadores del PDF")
    else:
        print("Buscando los capítulos en el texto de las páginas (puede tardar unos minutos)...")
        capitulos = capitulos_por_texto(reader)
        print(f"Encontré {len(capitulos)} capítulos en el texto")
    if not capitulos:
        sys.exit("No encontré capítulos. Mándale a Claude capturas del índice del libro.")

    numeros = [c[0] for c in capitulos]
    faltan = sorted(set(range(numeros[0], numeros[-1] + 1)) - set(numeros))
    if faltan:
        print(f"Aviso: no encontré los capítulos {faltan}; quedarán dentro del capítulo anterior.")

    if args.listar:
        for num, titulo, pagina in capitulos:
            print(f"  {num:3d}  pág. {pagina + 1:5d}  {titulo}")
        return

    carpeta = Path(args.salida)
    carpeta.mkdir(parents=True, exist_ok=True)
    if capitulos[0][2] > 0:
        guardar(reader, carpeta / "00_Preliminares_e_indice.pdf", 0, capitulos[0][2])
    for j, (num, titulo, inicio) in enumerate(capitulos):
        fin = capitulos[j + 1][2] if j + 1 < len(capitulos) else total
        nombre = re.sub(r"^cap[ií]tulo\s+\d+\s*[.:\-–—]?\s*", "", titulo, flags=re.IGNORECASE)
        nombre = re.sub(r"^\d{1,3}[\s.:\-]+", "", nombre)
        guardar(reader, carpeta / f"Cap_{num:02d}_{slug(nombre) or 'sin_titulo'}.pdf", inicio, fin)

    print(f"Listo. Archivos en: {carpeta.resolve()}")


if __name__ == "__main__":
    main()
