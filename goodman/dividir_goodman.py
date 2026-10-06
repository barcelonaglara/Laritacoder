#!/usr/bin/env python3
"""Divide el PDF del Goodman & Gilman (Las bases farmacológicas de la terapéutica)
en un PDF por capítulo, según el índice del libro.

Uso:
    pip install pypdf
    python dividir_goodman.py                      # busca el PDF solo en tu Drive (Colab)
    python dividir_goodman.py Goodman.pdf
    python dividir_goodman.py Goodman.pdf --por-seccion
    python dividir_goodman.py Goodman.pdf --offset 24

El índice usa números de página del libro. El PDF tiene además páginas previas
(portada, contenido, prefacio... en números romanos), así que
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

# (sección, título, página donde empieza la sección, [(capítulo, título, página), ...])
INDICE = [
    ("I", "Principios generales", 1, [
        (1, "La invención de fármacos y la industria farmacéutica", 3),
        (2, "Farmacocinética: dinámica de la absorción, distribución, metabolismo y eliminación de fármacos", 13),
        (3, "Farmacodinámica: mecanismos moleculares de la acción de los fármacos", 31),
        (4, "Toxicidad de fármacos y envenenamiento", 55),
        (5, "Transportadores de membrana y respuesta a los fármacos", 65),
        (6, "Metabolismo de las drogas", 85),
        (7, "Farmacogenética", 101),
    ]),
    ("II", "Neurofarmacología", 113, [
        (8, "Neurotransmisión: sistema nervioso motor autónomo y somático", 115),
        (9, "Agonistas y antagonistas del receptor muscarínico", 149),
        (10, "Agentes anticolinesterásicos", 163),
        (11, "La nicotina y los agentes que actúan en la unión neuromuscular y en los ganglios autonómicos", 177),
        (12, "Agonistas y antagonistas adrenérgicos", 191),
        (13, "5-hidroxitriptamina (serotonina) y dopamina", 225),
        (14, "La neurotransmisión en el sistema nervioso central", 243),
        (15, "Tratamiento farmacológico de trastornos de depresión y ansiedad", 267),
        (16, "Farmacoterapia de la psicosis y la manía", 279),
        (17, "Farmacoterapia de la epilepsia", 303),
        (18, "Tratamiento de los trastornos degenerativos del sistema nervioso central", 327),
        (19, "Hipnóticos y sedantes", 339),
        (20, "Opioides, analgesia y control del dolor", 355),
        (21, "Anestésicos generales y gases terapéuticos", 387),
        (22, "Anestésicos locales", 405),
        (23, "Etanol", 421),
        (24, "Trastornos del uso de drogas y adicción", 433),
    ]),
    ("III", "Modulación de la función pulmonar, renal y cardiovascular", 443, [
        (25, "Fármacos que afectan la función excretora renal", 445),
        (26, "Renina y angiotensina", 471),
        (27, "Tratamiento de la cardiopatía isquémica", 489),
        (28, "Tratamiento de la hipertensión", 507),
        (29, "Terapia de insuficiencia cardiaca", 527),
        (30, "Fármacos antiarrítmicos", 547),
        (31, "Tratamiento de la hipertensión arterial pulmonar", 573),
        (32, "Coagulación sanguínea y anticoagulantes, fibrinolíticos y antiagregantes plaquetarios", 585),
        (33, "Terapia medicamentosa para las dislipidemias", 605),
    ]),
    ("IV", "Inflamación, inmunomodulación y hematopoyesis", 619, [
        (34, "Introducción a la inmunidad y la inflamación", 621),
        (35, "Inmunosupresores y tolerógenos", 637),
        (36, "Inmunoglobulinas y vacunas", 655),
        (37, "Autacoides derivados de los lípidos: eicosanoides y factor activador de plaquetas", 673),
        (38, "Farmacoterapia de inflamación, fiebre, dolor y gota", 685),
        (39, "Histamina, bradicinina y sus antagonistas", 711),
        (40, "Farmacología pulmonar", 727),
        (41, "Fármacos hematopoyéticos: factores de crecimiento, minerales y vitaminas", 751),
    ]),
    ("V", "Hormonas y antagonistas hormonales", 769, [
        (42, "Introducción a la endocrinología: eje hipotálamo-hipófisis", 771),
        (43, "Tiroides y fármacos antitiroideos", 787),
        (44, "Estrógenos, progestinas y tracto reproductor femenino", 803),
        (45, "Andrógenos y tracto reproductor masculino", 833),
        (46, "Hormona adrenocorticotrópica, esteroides suprarrenales y corteza suprarrenal", 845),
        (47, "Páncreas endocrino y farmacoterapia de la diabetes mellitus y la hipoglucemia", 863),
        (48, "Fármacos que modifican la homeostasis de iones minerales y el recambio óseo", 887),
    ]),
    ("VI", "Farmacología gastrointestinal", 907, [
        (49, "Farmacoterapia de la acidez gástrica, úlceras pépticas y enfermedad por reflujo gastroesofágico", 909),
        (50, "Motilidad gastrointestinal y flujo de agua; antieméticos; enfermedad biliar y pancreática", 921),
        (51, "Farmacoterapia de la enfermedad intestinal inflamatoria", 945),
    ]),
    ("VII", "Quimioterapia de enfermedades infecciosas", 955, [
        (52, "Principios generales del tratamiento antimicrobiano", 957),
        (53, "Tratamiento farmacológico del paludismo", 969),
        (54, "Tratamiento farmacológico de las infecciones por protozoarios", 987),
        (55, "Tratamiento farmacológico de las helmintosis", 1001),
        (56, "Sulfonamidas, trimetoprim-sulfametoxazol, quinolonas y fármacos para las infecciones de vías urinarias", 1011),
        (57, "Penicilinas, cefalosporinas y otros antibióticos lactámicos β", 1023),
        (58, "Aminoglucósidos", 1039),
        (59, "Inhibidores de la síntesis de proteínas y diversos agentes antibacterianos", 1049),
        (60, "Quimioterapia de la tuberculosis, la enfermedad causada por el complejo Mycobacterium avium y la lepra", 1067),
        (61, "Agentes antimicóticos", 1087),
        (62, "Agentes antivirales (no retrovirales)", 1105),
        (63, "Tratamiento de la hepatitis viral (HBV/HCV)", 1119),
        (64, "Antirretrovirales y tratamiento de la infección por VIH", 1137),
    ]),
    ("VIII", "Farmacoterapia de enfermedades neoplásicas", 1159, [
        (65, "Principios generales en la farmacología contra el cáncer", 1161),
        (66, "Fármacos citotóxicos", 1167),
        (67, "Terapias dirigidas: anticuerpos monoclonales, inhibidores de la proteína cinasa y varias moléculas pequeñas", 1203),
        (68, "Hormonas y fármacos relacionados en la terapia contra el cáncer", 1237),
    ]),
    ("IX", "Farmacología de sistemas especiales", 1249, [
        (69, "Farmacología ocular", 1251),
        (70, "Farmacología dermatológica", 1271),
        (71, "Toxicología ambiental: cancerígenos y metales pesados", 1297),
    ]),
    ("Apendices", "Apéndices e índice alfabético", 1317, [
        ("Apendice_I", "Principios de redacción de la receta médica y la conformidad del paciente", 1317),
        ("Apendice_II", "Diseño y optimización de los regímenes posológicos: datos farmacocinéticos", 1325),
        ("Indice", "alfabético", 1379),
    ]),
]

# Capítulos con títulos poco genéricos, usados para detectar el offset por texto.
ANCLAS = [4, 9, 16, 33, 43, 53, 61, 69]


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).lower()


def slug(texto, largo=60):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^A-Za-z0-9]+", "_", texto).strip("_")
    return texto[:largo].rstrip("_")


def buscar_en_drive():
    """En Colab, busca un PDF con "goodman" en el nombre dentro de Mi unidad."""
    raiz = Path("/content/drive/MyDrive")
    if not raiz.exists():
        return None
    encontrados = sorted(p for p in raiz.iterdir() if p.is_file() and "goodman" in p.name.lower())
    if encontrados:
        print("Encontré en tu Drive:", *[f"  {p}" for p in encontrados], sep="\n")
    return encontrados[0] if encontrados else None


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
    capitulos = {num: (titulo, pag) for _, _, _, caps in INDICE for num, titulo, pag in caps}
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


def bloques(por_seccion):
    """Devuelve [(nombre_archivo o None, página_libro_inicio)] en orden.
    Las portadillas de sección (None) no se exportan en modo capítulo, pero
    marcan dónde termina el capítulo anterior."""
    salida = []
    for i, (sec, titulo_sec, pag_sec, caps) in enumerate(INDICE, start=1):
        if por_seccion:
            salida.append((f"Seccion_{i:02d}_{sec}_{slug(titulo_sec)}", pag_sec))
            continue
        if pag_sec < caps[0][2]:
            salida.append((None, pag_sec))
        for num, titulo, pag in caps:
            prefijo = f"Cap_{num:02d}" if isinstance(num, int) else num
            salida.append((f"{prefijo}_{slug(titulo)}", pag))
    return salida


def guardar(reader, ruta, inicio, fin):
    """Guarda las páginas [inicio, fin) (índices base 0) en ruta."""
    writer = PdfWriter()
    for idx in range(inicio, fin):
        writer.add_page(reader.pages[idx])
    with open(ruta, "wb") as f:
        writer.write(f)
    tam = ruta.stat().st_size / 1e6
    print(f"  {ruta.name}: páginas PDF {inicio + 1}-{fin} ({fin - inicio} págs., {tam:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Divide el Goodman en capítulos.")
    parser.add_argument("pdf", nargs="?", help="Ruta al PDF (si no la das, lo busca en tu Drive)")
    parser.add_argument("--salida", help="Carpeta de salida")
    parser.add_argument("--offset", type=int, help="página_pdf = página_libro + offset")
    parser.add_argument("--por-seccion", action="store_true", help="Un PDF por sección en vez de por capítulo")
    parser.add_argument("--incluir-preliminares", action="store_true", help="Exporta también portada, contenido y prefacio")
    args = parser.parse_args()

    ruta = Path(args.pdf) if args.pdf else None
    if ruta is None or not ruta.exists():
        if ruta is not None:
            print(f"No existe {ruta}; lo busco en tu Drive...")
        ruta = buscar_en_drive()
        if ruta is None:
            sys.exit("No encontré el PDF del Goodman. Pasa la ruta exacta "
                     "(en Colab: carpeta → drive → MyDrive → ⋮ junto al archivo → Copiar ruta).")
    print(f"Usando: {ruta}")

    reader = PdfReader(str(ruta))
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

    if args.salida:
        carpeta = Path(args.salida)
    elif Path("/content/drive/MyDrive").exists():
        carpeta = Path("/content/drive/MyDrive/Goodman_capitulos")
    else:
        carpeta = Path("goodman_capitulos")
    carpeta.mkdir(parents=True, exist_ok=True)

    lista = bloques(args.por_seccion)
    if args.incluir_preliminares and offset > 0:
        guardar(reader, carpeta / "00_Preliminares_y_contenido.pdf", 0, offset)

    for i, (nombre, pag) in enumerate(lista):
        if nombre is None:
            continue
        inicio = pag - 1 + offset
        fin = lista[i + 1][1] - 1 + offset if i + 1 < len(lista) else total
        if inicio >= total:
            print(f"  ! {nombre}: empieza fuera del PDF (pág. {inicio + 1}), se omite")
            continue
        guardar(reader, carpeta / f"{nombre}.pdf", inicio, min(fin, total))

    print(f"Listo. Archivos en: {carpeta.resolve()}")


if __name__ == "__main__":
    main()
