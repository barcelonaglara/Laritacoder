# Dividir el Goodman en capítulos

`dividir_goodman.py` corta el PDF del Goodman & Gilman en un PDF por capítulo
(71 capítulos, 2 apéndices y el índice alfabético), según el índice del libro.

## En Google Colab

1. Sube `dividir_goodman.py` (carpeta 📁 de la izquierda → subir).
2. Ejecuta:

```python
from google.colab import drive
drive.mount('/content/drive')
!pip install -q pypdf
!python dividir_goodman.py
```

Busca solo el PDF del Goodman en "Mi unidad" y deja los capítulos en la
carpeta `Goodman_capitulos` de tu Drive.

## Opciones

- `ruta/al/libro.pdf`: si quieres indicar el PDF a mano.
- `--por-seccion`: un PDF por sección en vez de por capítulo.
- `--offset N`: si no detecta solo dónde empieza la página 1 del libro.
  N = (página del PDF donde está la página 1 del libro) − 1.
- `--incluir-preliminares`: exporta también portada, contenido y prefacio.
- `--salida CARPETA`: carpeta donde guardar los PDFs.
