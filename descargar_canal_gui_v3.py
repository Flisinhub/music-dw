import tkinter as tk
from tkinter import filedialog, messagebox
import yt_dlp
import os
import threading

def seleccionar_carpeta():
    carpeta = filedialog.askdirectory(title="Elige carpeta para los MP3")
    if carpeta:
        entry_ruta.delete(0, tk.END)
        entry_ruta.insert(0, carpeta)

def seleccionar_ffmpeg():
    carpeta = filedialog.askdirectory(title="Carpeta que contiene ffmpeg.exe y ffprobe.exe")
    if carpeta:
        entry_ffmpeg.delete(0, tk.END)
        entry_ffmpeg.insert(0, carpeta)

def iniciar_descarga():
    url = entry_url.get().strip()
    ruta = entry_ruta.get().strip()
    ruta_ffmpeg = entry_ffmpeg.get().strip()
    
    if not url or not ruta:
        messagebox.showerror("Error", "¡Pega la URL y elige carpeta!")
        return
    
    btn_iniciar.config(state="disabled")
    label_status.config(text="🚀 Descargando SIN login (modo lento pero seguro)...", fg="orange")
    
    def descargar():
        try:
            os.makedirs(ruta, exist_ok=True)
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{ruta}/%(channel)s/%(title)s.%(ext)s',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}],
                'keepvideo': False,
                'embed_metadata': True,
                'embed_thumbnail': True,
                'ignoreerrors': True,
                'retries': 20,
                'sleep_interval': 8,                    # Más rápido que antes
                'download_archive': os.path.join(ruta, 'descargados.txt'),
                'quiet': False,
                'extractor_args': {'youtube': {
                    'player_client': ['web_safari', 'ios', 'web', 'android'], 
                    'skip': ['web_embedded']
                }}
            }
            
            if ruta_ffmpeg:
                ydl_opts['ffmpeg_location'] = ruta_ffmpeg
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            root.after(0, lambda: messagebox.showinfo("✅ ¡ÉXITO!", f"¡Todo en MP3 320kbps!\n\nCarpeta: {ruta}"))
            root.after(0, lambda: label_status.config(text="✅ ¡Terminado!", fg="green"))
            
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Error", f"Error:\n{str(e)}"))
            root.after(0, lambda: label_status.config(text="❌ Error", fg="red"))
        
        finally:
            root.after(0, lambda: btn_iniciar.config(state="normal"))
    
    threading.Thread(target=descargar, daemon=True).start()

# ==================== VENTANA SIMPLE ====================
root = tk.Tk()
root.title("🎵 Descargador YouTube MP3 - v5 (100% SIN login)")
root.geometry("700x400")
root.resizable(False, False)

tk.Label(root, text="Descargador de Canales → MP3 320kbps\n(SIN cuenta personal)", font=("Arial", 16, "bold")).pack(pady=20)

tk.Label(root, text="URL del canal:", font=("Arial", 10)).pack(anchor="w", padx=30)
entry_url = tk.Entry(root, width=80, font=("Arial", 11))
entry_url.pack(padx=30, pady=8)

tk.Label(root, text="Carpeta de descargas:", font=("Arial", 10)).pack(anchor="w", padx=30)
frame1 = tk.Frame(root)
frame1.pack(padx=30, pady=5, fill="x")
entry_ruta = tk.Entry(frame1, width=65, font=("Arial", 11))
entry_ruta.pack(side="left", fill="x", expand=True, padx=(0,5))
tk.Button(frame1, text="📁 Buscar", command=seleccionar_carpeta).pack(side="right")

tk.Label(root, text="Carpeta de FFmpeg:", font=("Arial", 10)).pack(anchor="w", padx=30)
frame2 = tk.Frame(root)
frame2.pack(padx=30, pady=5, fill="x")
entry_ffmpeg = tk.Entry(frame2, width=65, font=("Arial", 11))
entry_ffmpeg.pack(side="left", fill="x", expand=True, padx=(0,5))
tk.Button(frame2, text="📁 Buscar ffmpeg", command=seleccionar_ffmpeg).pack(side="right")

btn_iniciar = tk.Button(root, text="🚀 INICIAR DESCARGA (modo sin login)", font=("Arial", 14, "bold"), 
                       bg="#00cc00", fg="white", height=2, command=iniciar_descarga)
btn_iniciar.pack(pady=25)

label_status = tk.Label(root, text="✅ Modo 100% sin cuenta personal\n(Recomendado: instala Node.js primero para eliminar warnings)", 
                       font=("Arial", 10), fg="blue")
label_status.pack()

default_path = os.path.join(os.path.expanduser("~"), "Audios_YouTube")
entry_ruta.insert(0, default_path)

root.mainloop()