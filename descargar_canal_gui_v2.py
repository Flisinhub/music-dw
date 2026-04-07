import tkinter as tk
from tkinter import filedialog, messagebox
import yt_dlp
import os
import threading

def seleccionar_carpeta_descargas():
    carpeta = filedialog.askdirectory(title="Elige carpeta para guardar los MP3")
    if carpeta:
        entry_ruta.delete(0, tk.END)
        entry_ruta.insert(0, carpeta)

def seleccionar_ffmpeg():
    carpeta = filedialog.askdirectory(title="Selecciona la carpeta que contiene ffmpeg.exe y ffprobe.exe")
    if carpeta:
        entry_ffmpeg.delete(0, tk.END)
        entry_ffmpeg.insert(0, carpeta)

def iniciar_descarga():
    url = entry_url.get().strip()
    ruta_descargas = entry_ruta.get().strip()
    ruta_ffmpeg = entry_ffmpeg.get().strip()
    
    if not url or not ruta_descargas:
        messagebox.showerror("Error", "¡Pega la URL y elige carpeta de descargas!")
        return
    
    btn_iniciar.config(state="disabled")
    label_status.config(text="🚀 Iniciando descarga... (puede tardar horas)", fg="orange")
    
    def descargar():
        try:
            os.makedirs(ruta_descargas, exist_ok=True)
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{ruta_descargas}/%(channel)s/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'keepvideo': False,
                'embed_metadata': True,
                'embed_thumbnail': True,
                'ignoreerrors': True,
                'retries': 10,
                'sleep_interval': 2,
                'download_archive': os.path.join(ruta_descargas, 'descargados.txt'),
                'quiet': False,
            }
            
            # ←←← AÑADIMOS LA RUTA DE FFMPEG SI LA USUARIO LA ELIGIÓ
            if ruta_ffmpeg:
                ydl_opts['ffmpeg_location'] = ruta_ffmpeg
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            root.after(0, lambda: messagebox.showinfo("✅ ¡ÉXITO!", f"Todo descargado en MP3 320kbps\n\nCarpeta:\n{ruta_descargas}"))
            root.after(0, lambda: label_status.config(text="✅ ¡Terminado! Archivos en .mp3", fg="green"))
            
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Error", f"Error:\n{str(e)}"))
            root.after(0, lambda: label_status.config(text="❌ Error", fg="red"))
        
        finally:
            root.after(0, lambda: btn_iniciar.config(state="normal"))
    
    threading.Thread(target=descargar, daemon=True).start()

# ==================== VENTANA ====================
root = tk.Tk()
root.title("🎵 Descargador YouTube a MP3 320kbps (v2 con FFmpeg)")
root.geometry("700x420")
root.resizable(False, False)

tk.Label(root, text="Descargador de Canales YouTube → MP3", font=("Arial", 16, "bold")).pack(pady=15)

tk.Label(root, text="1. URL del canal:", font=("Arial", 10)).pack(anchor="w", padx=30)
entry_url = tk.Entry(root, width=85, font=("Arial", 11))
entry_url.pack(padx=30, pady=8)

tk.Label(root, text="2. Carpeta de descargas:", font=("Arial", 10)).pack(anchor="w", padx=30)
frame1 = tk.Frame(root)
frame1.pack(padx=30, pady=5, fill="x")
entry_ruta = tk.Entry(frame1, width=65, font=("Arial", 11))
entry_ruta.pack(side="left", fill="x", expand=True, padx=(0,5))
tk.Button(frame1, text="📁 Buscar", command=seleccionar_carpeta_descargas).pack(side="right")

tk.Label(root, text="3. Carpeta de FFmpeg (¡IMPORTANTE!):", font=("Arial", 10)).pack(anchor="w", padx=30)
frame2 = tk.Frame(root)
frame2.pack(padx=30, pady=5, fill="x")
entry_ffmpeg = tk.Entry(frame2, width=65, font=("Arial", 11))
entry_ffmpeg.pack(side="left", fill="x", expand=True, padx=(0,5))
tk.Button(frame2, text="📁 Buscar ffmpeg", command=seleccionar_ffmpeg).pack(side="right")

# Carpeta por defecto
default_path = os.path.join(os.path.expanduser("~"), "Audios_YouTube")
entry_ruta.insert(0, default_path)

btn_iniciar = tk.Button(root, text="🚀 INICIAR DESCARGA EN MP3", font=("Arial", 14, "bold"), 
                       bg="#00cc00", fg="white", height=2, command=iniciar_descarga)
btn_iniciar.pack(pady=25)

label_status = tk.Label(root, text="Pega URL → elige carpeta → busca la carpeta de FFmpeg → pulsa verde", font=("Arial", 10), fg="blue")
label_status.pack()

root.mainloop()