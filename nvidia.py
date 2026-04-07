import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import os
import threading
import subprocess

# ================== FUNCIONES AUXILIARES ==================

def buscar_ffmpeg(carpeta):
    """Devuelve la ruta a ffmpeg.exe/ffprobe.exe si existen en la carpeta."""
    ffmpeg_path = os.path.join(carpeta, "ffmpeg.exe")
    ffprobe_path = os.path.join(carpeta, "ffprobe.exe")
    if os.path.isfile(ffmpeg_path) and os.path.isfile(ffprobe_path):
        return carpeta
    return None

def ffmpeg_en_path():
    """Comprueba si ffmpeg está en el PATH del sistema."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def obtener_id_canal(url):
    """Intenta extraer el identificador de canal a partir de la URL."""
    if "/channel/" in url:
        return url.split("/channel/")[1].split("/")[0]
    if "/user/" in url:
        return url.split("/user/")[1].split("/")[0]
    if "/@" in url:
        return url.split("/@")[1].split("/")[0]
    return None

# ================== INTERFAZ ==================

root = tk.Tk()
root.title("🎵 Descargador YouTube → MP3 (mejorado)")
root.geometry("780x580")
root.resizable(False, False)

style = ttk.Style()
style.theme_use("clam")  # tema más moderno[web:48]

# Estilos generales
style.configure("TLabel", font=("Segoe UI", 10))
style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
style.configure("TButton", font=("Segoe UI", 10))
style.configure(
    "Accent.TButton",
    font=("Segoe UI", 11, "bold"),
    foreground="white",
    background="#0078D7",
    padding=6
)
style.map(
    "Accent.TButton",
    background=[("active", "#005A9E")]
)
style.configure(
    "Danger.TButton",
    font=("Segoe UI", 10, "bold"),
    foreground="white",
    background="#D83B01",
    padding=6
)
style.map(
    "Danger.TButton",
    background=[("active", "#A4262C")]
)

# Título
ttk.Label(
    root,
    text="Descargador de Canales YouTube → MP3",
    style="Title.TLabel"
).pack(pady=10)

main = ttk.Frame(root, padding="10 5 10 10")
main.pack(fill="both", expand=True)

# ---- 1. URL ----
ttk.Label(main, text="1. URL del canal / playlist / vídeo:")\
    .grid(row=0, column=0, sticky="w", pady=3)
entry_url = ttk.Entry(main, width=80)
entry_url.grid(row=0, column=1, pady=3, padx=5, sticky="we")

# ---- 2. Carpeta de descargas ----
ttk.Label(main, text="2. Carpeta de descargas:")\
    .grid(row=1, column=0, sticky="w", pady=3)
frame_ruta = ttk.Frame(main)
frame_ruta.grid(row=1, column=1, pady=3, padx=5, sticky="we")
entry_ruta = ttk.Entry(frame_ruta, width=60)
entry_ruta.pack(side="left", fill="x", expand=True)
def seleccionar_carpeta_descargas():
    carpeta = filedialog.askdirectory(title="Elige carpeta para guardar los MP3")
    if carpeta:
        entry_ruta.delete(0, tk.END)
        entry_ruta.insert(0, carpeta)
ttk.Button(frame_ruta, text="📁 Buscar", command=seleccionar_carpeta_descargas)\
    .pack(side="left", padx=5)

# ---- 3. Carpeta de FFmpeg ----
ttk.Label(main, text="3. Carpeta de FFmpeg (opcional):")\
    .grid(row=2, column=0, sticky="w", pady=3)
frame_ffmpeg = ttk.Frame(main)
frame_ffmpeg.grid(row=2, column=1, pady=3, padx=5, sticky="we")
entry_ffmpeg = ttk.Entry(frame_ffmpeg, width=60)
entry_ffmpeg.pack(side="left", fill="x", expand=True)
def seleccionar_ffmpeg():
    carpeta = filedialog.askdirectory(
        title="Selecciona la carpeta con ffmpeg.exe y ffprobe.exe"
    )
    if carpeta:
        entry_ffmpeg.delete(0, tk.END)
        entry_ffmpeg.insert(0, carpeta)
ttk.Button(frame_ffmpeg, text="📁 Buscar ffmpeg", command=seleccionar_ffmpeg)\
    .pack(side="left", padx=5)

# ---- 4. Calidad de audio ----
ttk.Label(main, text="4. Calidad de audio (kbps):")\
    .grid(row=3, column=0, sticky="w", pady=3)
calidad_var = tk.StringVar(value="320")
calidad_cb = ttk.Combobox(
    main,
    textvariable=calidad_var,
    values=["128", "192", "256", "320"],
    width=6,
    state="readonly"
)
calidad_cb.grid(row=3, column=1, pady=3, padx=5, sticky="w")

# ---- Progreso ----
ttk.Label(main, text="Progreso:")\
    .grid(row=4, column=0, sticky="w", pady=(10, 3))
progress = ttk.Progressbar(main, orient="horizontal",
                           mode="determinate", length=520)
progress.grid(row=4, column=1, pady=(10, 3), padx=5, sticky="we")

# ---- Log ----
ttk.Label(main, text="Log de operaciones:")\
    .grid(row=5, column=0, sticky="nw", pady=(10, 3))
text_log = tk.Text(
    main,
    width=86,
    height=13,
    state="disabled",
    bg="#f8f8f8",
    relief="solid",
    bd=1
)
text_log.grid(row=5, column=1, pady=(10, 3), padx=5, sticky="we")
scroll_log = ttk.Scrollbar(main, orient="vertical", command=text_log.yview)
scroll_log.grid(row=5, column=2, sticky="ns", pady=(10, 3))
text_log.configure(yscrollcommand=scroll_log.set)

def log(msg):
    text_log.configure(state="normal")
    text_log.insert(tk.END, msg + "\n")
    text_log.see(tk.END)
    text_log.configure(state="disabled")

# ---- Botones ----
btn_frame = ttk.Frame(main)
btn_frame.grid(row=6, column=0, columnspan=3, pady=15)

btn_iniciar = ttk.Button(btn_frame, text="🚀 INICIAR DESCARGA",
                         style="Accent.TButton")
btn_iniciar.pack(side="left", padx=5)

btn_detener = ttk.Button(btn_frame, text="⏹ DETENER",
                         style="Danger.TButton", state="disabled")
btn_detener.pack(side="left", padx=5)

ttk.Button(btn_frame, text="Salir", command=root.quit)\
    .pack(side="left", padx=5)

# Ruta por defecto
default_path = os.path.join(os.path.expanduser("~"), "Audios_YouTube")
entry_ruta.insert(0, default_path)

# ================== LÓGICA DE DESCARGA ==================

descarga_activa = threading.Event()
descarga_cancelada = threading.Event()

def progreso_hook(d):
    """Actualiza barra de progreso y log usando el hook de yt_dlp[web:42]."""
    if descarga_cancelada.is_set():
        raise yt_dlp.utils.DownloadError("Descarga cancelada por el usuario")

    if d.get("status") == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        if total:
            porcentaje = d["downloaded_bytes"] / total * 100
            speed = d.get("speed") or 0
            eta = d.get("eta") or 0
            root.after(0, lambda: progress.configure(value=porcentaje))
            root.after(
                0,
                lambda: log(
                    f"⬇ {os.path.basename(d['filename'])} "
                    f"{porcentaje:5.1f}%  "
                    f"{speed/1024:6.1f} KiB/s  ETA {eta:4d}s"
                )
            )
    elif d.get("status") == "finished":
        root.after(
            0,
            lambda: log(f"✅ Convertido a MP3: {os.path.basename(d['filename'])}")
        )

def iniciar_descarga():
    url = entry_url.get().strip()
    carpeta = entry_ruta.get().strip()
    carpeta_ffmpeg = entry_ffmpeg.get().strip()
    calidad = calidad_var.get()

    if not url or not carpeta:
        messagebox.showerror(
            "Error",
            "Debes pegar la URL y elegir la carpeta de descargas."
        )
        return

    os.makedirs(carpeta, exist_ok=True)
    archive_file = os.path.join(carpeta, "descargados.txt")

    # Localizar FFmpeg
    ffmpeg_location = None
    if carpeta_ffmpeg:
        ffmpeg_location = buscar_ffmpeg(carpeta_ffmpeg)
        if not ffmpeg_location:
            messagebox.showwarning(
                "Advertencia",
                "No se encontró ffmpeg.exe/ffprobe.exe en la carpeta indicada."
            )
    if not ffmpeg_location and ffmpeg_en_path():
        ffmpeg_location = None  # yt_dlp lo coge del PATH

    # Si es un canal, transformar en lista de subidas
    if "youtube.com" in url and ("/channel/" in url or "/user/" in url or "/@" in url):
        canal_id = obtener_id_canal(url)
        if canal_id:
            url_canal = f"https://www.youtube.com/channel/{canal_id}/videos"
            log(f"🔎 Detectado canal → usando URL: {url_canal}")
            url_final = url_canal
        else:
            log("⚠️ No se pudo extraer el ID del canal; se usará la URL tal cual.")
            url_final = url
    else:
        url_final = url

    # Opciones de yt_dlp, con plantilla Artista - Título[web:42][web:43]
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(
            carpeta,
            "%(artist,creator,channel)s - %(track,title)s.%(ext)s"
        ),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": calidad,
        }],
        "keepvideo": False,
        "embed_metadata": True,
        "embed_thumbnail": True,
        "ignoreerrors": True,
        "retries": 10,
        "fragment_retries": 10,
        "sleep_interval": 1,
        "max_sleep_interval": 5,
        "download_archive": archive_file,
        "progress_hooks": [progreso_hook],
        "quiet": True,
        "no_warnings": True,
    }
    if ffmpeg_location:
        ydl_opts["ffmpeg_location"] = ffmpeg_location

    # Desactivar controles
    btn_iniciar.config(state="disabled")
    btn_detener.config(state="normal")
    descarga_activa.set()
    descarga_cancelada.clear()
    progress.configure(value=0)
    log("🚀 Iniciando descarga...")

    def tarea():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url_final])
            log("✅ ¡Descarga completada!")
            messagebox.showinfo(
                "Éxito",
                f"Todos los audios se guardaron en:\n{carpeta}"
            )
        except yt_dlp.utils.DownloadError as e:
            if "cancelada" in str(e):
                log("⏹ Descarga cancelada por el usuario.")
            else:
                log(f"❌ Error de descarga: {e}")
                messagebox.showerror(
                    "Error",
                    f"Falló la descarga:\n{e}"
                )
        except Exception as e:
            log(f"❌ Error inesperado: {e}")
            messagebox.showerror(
                "Error",
                f"Ocurrió un error inesperado:\n{e}"
            )
        finally:
            root.after(0, lambda: btn_iniciar.config(state="normal"))
            root.after(0, lambda: btn_detener.config(state="disabled"))
            root.after(0, lambda: descarga_activa.clear())
            root.after(0, lambda: progress.configure(value=0))

    threading.Thread(target=tarea, daemon=True).start()

def detener_descarga():
    if descarga_activa.is_set():
        descarga_cancelada.set()
        log("⏹ Solicitando cancelación...")

btn_iniciar.config(command=iniciar_descarga)
btn_detener.config(command=detener_descarga)

root.mainloop()
