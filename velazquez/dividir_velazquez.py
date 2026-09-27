#!/usr/bin/env python3
"""Divide el PDF de "Farmacología Básica y Clínica" (Velázquez) por secciones.

Uso:
    pip install pypdf
    python dividir_velazquez.py Velazquez.pdf
    python dividir_velazquez.py Velazquez.pdf --por-capitulo
    python dividir_velazquez.py Velazquez.pdf --offset 26 --salida mis_secciones

El índice de capítulos usa números de página del libro. El PDF tiene además
páginas previas (portada, prólogo, índice en números romanos...), así que
página_pdf = página_libro + offset. El script intenta detectar el offset solo;
si no lo consigue, pásalo con --offset (mira en qué página del visor aparece
la página 1 del libro y réstale 1).
"""

import argparse
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from pypdf import PdfReader, PdfWriter

# (sección, título, [(capítulo, título, página del libro), ...])
# La sección I y la Parte 2 no salen completas en las capturas del índice:
# se exportan como un único bloque cada una.
INDICE = [
    ("I", "Sección I", [
        (1, "Capítulos 1 a 4", 1),
    ]),
    ("II", "Sistema nervioso periférico", [
        (5, "Introducción a la farmacología del sistema nervioso autónomo", 95),
        (6, "Sistema nervioso parasimpático: fármacos colinomiméticos", 115),
        (7, "Sistema nervioso autónomo: fármacos antagonistas muscarínicos", 125),
        (8, "Neurotransmisión adrenérgica. Sistema nervioso simpático: fármacos simpaticomiméticos", 137),
        (9, "Sistema nervioso simpático: fármacos simpaticolíticos", 153),
        (10, "Fármacos anestésicos locales", 167),
    ]),
    ("III", "Sistema nervioso central", [
        (11, "Introducción a la farmacología del sistema nervioso central: neurotransmisores, receptores y otros elementos sinápticos", 179),
        (12, "Fármacos analgésicos opioides", 209),
        (13, "Fármacos anestésicos generales", 223),
        (14, "Fármacos anticonvulsivantes y antiepilépticos", 237),
        (15, "Fármacos en la enfermedad de Parkinson", 259),
        (16, "Fármacos ansiolíticos e hipnóticos", 271),
        (17, "Fármacos antipsicóticos", 287),
        (18, "Fármacos antidepresivos y antimaníacos", 299),
        (19, "Farmacología de la enfermedad de Alzheimer y de la enfermedad cerebrovascular. Fármacos psicoestimulantes y nootropos", 311),
        (20, "Drogas de abuso", 325),
    ]),
    ("IV", "Aparato cardiovascular", [
        (21, "Fármacos con efecto inotrópico positivo", 345),
        (22, "Fármacos antiarrítmicos", 359),
        (23, "Fármacos que actúan sobre el sistema renina-angiotensina", 377),
        (24, "Fármacos diuréticos", 395),
        (25, "Fármacos vasodilatadores. Antagonistas del calcio", 411),
        (26, "Fármacos antianginosos", 431),
        (27, "Fármacos hipolipemiantes", 445),
    ]),
    ("V", "Autacoides, inflamación y respuesta inmunológica", [
        (28, "Serotonina y fármacos que actúan sobre el sistema serotoninérgico. Purinas", 461),
        (29, "Histamina y fármacos antihistamínicos. Farmacología de otros mediadores inflamatorios", 471),
        (30, "Farmacología de los eicosanoides", 485),
        (31, "Fármacos antiinflamatorios no esteroideos y otros analgésicos-antipiréticos", 497),
        (32, "Fármacos antirreumáticos y antigotosos", 519),
        (33, "Fármacos inmunomoduladores", 531),
    ]),
    ("VI", "Aparato digestivo", [
        (34, "Farmacología de las secreciones gastrointestinales", 549),
        (35, "Farmacología de la motilidad gastrointestinal, del vómito y de la enfermedad inflamatoria intestinal", 563),
    ]),
    ("VII", "Sistema endocrino", [
        (36, "Fármacos que actúan en el eje hipotálamo-hipofisario. Farmacología del tiroides", 581),
        (37, "Fármacos antidiabéticos. Insulinas y antidiabéticos orales", 597),
        (38, "Farmacología de los esteroides sexuales y sus antagonistas. Anticonceptivos hormonales. Farmacología uterina", 611),
        (39, "Farmacología de la corteza suprarrenal", 631),
        (40, "Farmacología del calcio y del hueso", 647),
    ]),
    ("VIII", "Aparato respiratorio", [
        (41, "Fármacos antitusígenos, expectorantes y mucolíticos", 657),
        (42, "Fármacos broncodilatadores y antiinflamatorios en el asma y la enfermedad pulmonar obstructiva crónica", 667),
    ]),
    ("IX", "Sangre", [
        (43, "Fármacos antianémicos. Factores de crecimiento hemopoyético", 681),
        (44, "Farmacología de la trombosis y la hemostasia", 695),
    ]),
    ("X", "Quimioterapia antiinfecciosa y antitumoral", [
        (45, "Antibióticos. Generalidades", 715),
        (46, "Antibióticos β-lactámicos", 729),
        (47, "Antibióticos aminoglucósidos, tetraciclinas, tigeciclina y cloranfenicol", 751),
        (48, "Antibióticos macrólidos y otros antibióticos", 771),
        (49, "Sulfamidas y trimetoprima. Quinolonas", 789),
        (50, "Fármacos antituberculosos y antileprosos", 807),
        (51, "Antisépticos", 821),
        (52, "Fármacos antiparasitarios", 831),
        (53, "Fármacos antivíricos", 857),
        (54, "Fármacos antifúngicos", 891),
        (55, "Fármacos antineoplásicos", 909),
    ]),
    ("XI", "Temas especiales", [
        (56, "Fármacos de uso diagnóstico", 931),
        (57, "Vitaminas. Fitoterapia", 943),
        (58, "Terapias avanzadas", 957),
        (59, "Farmacología ocular", 969),
        (60, "Farmacología de la piel", 985),
    ]),
    ("XII+", "Parte 2 - Farmacología clínica", [
        (61, "Capítulo 61 en adelante", 997),
    ]),
]

# Capítulos con títulos poco genéricos, usados para detectar el offset por texto.
ANCLAS = [21, 24, 44, 46, 51, 53, 57]


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).lower()


def slug(texto, largo=60):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^A-Za-z0-9]+", "_", texto).strip("_")
    return texto[:largo].rstrip("_")


def offset_por_etiquetas(reader):
    """Si el PDF tiene etiquetas de página (i, ii, ... 1, 2, ...), usa la del "1"."""
    try:
        etiquetas = reader.page_labels
    except Exception:
        return None
    for i, etiqueta in enumerate(etiquetas):
        if etiqueta == "1" and i > 0:
            return i - 1
    return None


def offset_por_texto(reader, max_offset=120):
    """Busca el inicio de varios capítulos conocidos y devuelve el offset más votado."""
    capitulos = {num: (titulo, pag) for _, _, caps in INDICE for num, titulo, pag in caps}
    votos = Counter()
    n = len(reader.pages)
    for num in ANCLAS:
        titulo, pag = capitulos[num]
        clave = normalizar(titulo)[:30]
        for off in range(0, max_offset + 1):
            idx = pag - 1 + off
            if idx >= n:
                break
            try:
                texto = normalizar(reader.pages[idx].extract_text() or "")
            except Exception:
                continue
            if clave in texto:
                votos[off] += 1
                break
    if not votos:
        return None
    offset, cuantos = votos.most_common(1)[0]
    return offset if cuantos >= 2 else None


def bloques(por_capitulo):
    """Devuelve [(nombre_archivo, página_libro_inicio)] en orden."""
    salida = []
    for i, (sec, titulo_sec, caps) in enumerate(INDICE, start=1):
        if por_capitulo:
            for num, titulo, pag in caps:
                salida.append((f"Cap_{num:02d}_{slug(titulo)}", pag))
        else:
            nombre = f"Seccion_{i:02d}_{sec.replace('+', '')}_{slug(titulo_sec)}"
            salida.append((nombre, caps[0][2]))
    return salida


def main():
    parser = argparse.ArgumentParser(description="Divide el Velázquez por secciones.")
    parser.add_argument("pdf", help="Ruta al PDF del Velázquez")
    parser.add_argument("--salida", default="velazquez_secciones", help="Carpeta de salida")
    parser.add_argument("--offset", type=int, help="página_pdf = página_libro + offset")
    parser.add_argument("--por-capitulo", action="store_true", help="Un PDF por capítulo en vez de por sección")
    parser.add_argument("--incluir-preliminares", action="store_true", help="Exporta también las páginas previas a la 1")
    args = parser.parse_args()

    reader = PdfReader(args.pdf)
    total = len(reader.pages)
    print(f"PDF con {total} páginas")

    offset = args.offset
    if offset is None:
        offset = offset_por_etiquetas(reader)
        if offset is not None:
            print(f"Offset detectado por etiquetas de página: {offset}")
    if offset is None:
        print("Buscando el offset por el texto de los capítulos (puede tardar un poco)...")
        offset = offset_por_texto(reader)
        if offset is not None:
            print(f"Offset detectado por texto: {offset}")
    if offset is None:
        sys.exit("No pude detectar el offset. Mira en qué página del PDF empieza la página 1 "
                 "del libro y ejecuta de nuevo con --offset <esa página - 1>.")

    carpeta = Path(args.salida)
    carpeta.mkdir(parents=True, exist_ok=True)

    lista = bloques(args.por_capitulo)
    if args.incluir_preliminares and offset > 0:
        guardar(reader, carpeta / "00_Preliminares_e_indice.pdf", 0, offset)

    for i, (nombre, pag) in enumerate(lista):
        inicio = pag - 1 + offset
        fin = lista[i + 1][1] - 1 + offset if i + 1 < len(lista) else total
        if inicio >= total:
            print(f"  ! {nombre}: empieza fuera del PDF (pág. {inicio + 1}), se omite")
            continue
        guardar(reader, carpeta / f"{nombre}.pdf", inicio, min(fin, total))

    print(f"Listo. Archivos en: {carpeta.resolve()}")


def guardar(reader, ruta, inicio, fin):
    """Guarda las páginas [inicio, fin) (índices base 0) en ruta."""
    writer = PdfWriter()
    for idx in range(inicio, fin):
        writer.add_page(reader.pages[idx])
    with open(ruta, "wb") as f:
        writer.write(f)
    print(f"  {ruta.name}: páginas PDF {inicio + 1}-{fin} ({fin - inicio} págs.)")


if __name__ == "__main__":
    main()
