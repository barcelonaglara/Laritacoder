# Dividir el Goodman en capítulos

`dividir_goodman.py` corta el PDF del Goodman & Gilman en un PDF por capítulo.
No necesita el índice: usa los marcadores del PDF o, si no los tiene, busca
"Capítulo N" en el texto de las páginas.

## En Google Colab

1. Sube `dividir_goodman.py` (carpeta 📁 de la izquierda → subir).
2. Ejecuta primero esto para ver qué capítulos encuentra (no crea archivos):

```python
from google.colab import drive
drive.mount('/content/drive')
!pip install -q pypdf
!python dividir_goodman.py "/content/drive/MyDrive/Goodman" --listar
```

3. Si la lista está bien, divide el libro:

```python
!python dividir_goodman.py "/content/drive/MyDrive/Goodman" --salida "/content/drive/MyDrive/Goodman_capitulos"
```

## Opciones

- `--listar`: solo muestra los capítulos encontrados.
- `--por-texto`: ignora los marcadores del PDF y busca en el texto.
- `--salida CARPETA`: carpeta donde guardar los PDFs.
