# Descargador de YouTube MP3 / MP4

Aplicación de escritorio para Windows con una cola de descargas de vídeos,
canales y listas de reproducción.

## Dependencias

- Python 3.13 o posterior.
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) y `yt-dlp-ejs`, instalados con:

  ```powershell
  python -m pip install -r requirements-downloader.txt
  ```

- [FFmpeg](https://ffmpeg.org/) con `ffmpeg.exe` y `ffprobe.exe` para
  convertir el audio y combinar pistas de vídeo.
- Node.js para la extracción de JavaScript de YouTube cuando se ejecuta el
  script directamente. El ejecutable portátil de PyInstaller incluye `node.exe`.

## Ejecutar desde el código fuente

```powershell
python .\downloader-mp4-modificado.py
```

La aplicación busca FFmpeg junto al programa o en `PATH`; también permite
seleccionar su carpeta desde la interfaz.

## Crear el ejecutable portátil en Windows

Instala las dependencias de compilación:

```powershell
python -m pip install -r requirements-build-downloader.txt
```

Indica dónde están FFmpeg y Node.js y compila:

```powershell
$env:FFMPEG_DIR = "C:\ruta\a\ffmpeg"
$env:NODE_EXE = "C:\ruta\a\node.exe"
python -m PyInstaller --clean --noconfirm `
  --distpath .\downloader-mp4-portable `
  --workpath .\downloader-mp4-build\work `
  .\downloader-mp4-modificado.spec
```

El programa y las dependencias empaquetadas quedarán en
`downloader-mp4-portable\downloader-mp4-modificado\`. Distribuye la carpeta
completa, no solamente el `.exe`.

## Avisos de distribución

La compilación de FFmpeg utilizada para crear una distribución determina las
obligaciones de licencia aplicables. La compilación de Gyan indicada en
`THIRD_PARTY_NOTICES.txt` declara GPLv3 o posterior; sus dos ejecutables, por
separado, no incluyen el código fuente completo correspondiente de FFmpeg, sus
dependencias y los scripts de compilación. **No distribuyas un paquete creado
con esos binarios hasta obtener e incluir el código fuente correspondiente y
los avisos necesarios, o cumplir por otra vía la GPLv3.**

La compilación portátil local, si existe, es un artefacto de prueba y no se
incluye en el repositorio. Revisa `THIRD_PARTY_NOTICES.txt` antes de distribuir
binarios a otras personas.
