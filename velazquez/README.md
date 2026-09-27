# Dividir el Velázquez por secciones

`dividir_velazquez.py` corta el PDF de *Farmacología Básica y Clínica* (Velázquez)
en un PDF por sección del índice (o por capítulo con `--por-capitulo`).

## Opción fácil: Google Colab (el PDF ya está en tu Drive)

1. Abre https://colab.research.google.com y crea un cuaderno nuevo.
2. Sube `dividir_velazquez.py` (icono de carpeta a la izquierda → subir).
3. Ejecuta en una celda:

```python
from google.colab import drive
drive.mount('/content/drive')
!pip install -q pypdf
!python dividir_velazquez.py "/content/drive/MyDrive/Velazquez" --salida "/content/drive/MyDrive/Velazquez_secciones"
```

Los PDFs aparecerán en la carpeta `Velazquez_secciones` de tu Drive.

## En tu ordenador

```bash
pip install pypdf
python dividir_velazquez.py Velazquez.pdf
```

## Opciones

- `--por-capitulo`: un PDF por capítulo (archivos más pequeños).
- `--offset N`: si no detecta solo dónde empieza la página 1 del libro.
  N = (página del PDF donde está la página 1 del libro) − 1.
- `--incluir-preliminares`: exporta también portada, prólogo e índice.
- `--salida CARPETA`: carpeta donde guardar los PDFs.

La Sección I (capítulos 1–4) no se exporta. La Parte 2 (capítulo 61 en adelante)
sale como un solo bloque, porque no aparecía completa en las capturas del índice.
