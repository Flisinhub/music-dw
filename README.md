# Empaquetado del `nvidia claud 3.py`

Este proyecto usa `yt-dlp` y necesita `ffmpeg.exe`/`ffprobe.exe` para convertir los archivos a MP3.

## Pasos para generar el `.exe`

1. Coloca `ffmpeg.exe` y `ffprobe.exe` dentro de una carpeta llamada `ffmpeg` en la raíz del proyecto.
   - Debe quedar así:
     - `e:\Musica Makina\Audios_YouTube\ffmpeg\ffmpeg.exe`
     - `e:\Musica Makina\Audios_YouTube\ffmpeg\ffprobe.exe`

2. Ejecuta el script de construcción:
   - Haz doble clic en `build_exe.bat`
   - O ejecuta en PowerShell:
     ```powershell
     cd "e:\Musica Makina\Audios_YouTube"
     .\build_exe.bat
     ```

3. El ejecutable se generará en `dist\nvidia claud 3.exe`.

## Requisitos

- Python 3.13
- `yt-dlp`
- `pyinstaller`
- `ffmpeg` para Windows

## Uso del ejecutable

- El ejecutable busca `ffmpeg.exe` en:
  - la carpeta `ffmpeg` junto al exe
  - el PATH del sistema
  - la carpeta del propio ejecutable

- Si no tienes `ffmpeg`, descárgalo desde una fuente confiable y coloca `ffmpeg.exe` y `ffprobe.exe` en la carpeta `ffmpeg`.
