import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import os
import threading
import subprocess

# ================== FUNCIONES AUXILIARES ==================

def buscar_ffmpeg(carpeta):
    ffmpeg_path = os.path.join(carpeta, "ffmpeg.exe")
    ffprobe_path = os.path.join(carpeta, "ffprobe.exe")
    if os.path.isfile(ffmpeg_path) and os.path.isfile(ffprobe_path):
        return carpeta
    return None

def ffmpeg_en_path():
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
    if "/channel/" in url:
        return url.split("/channel/")[1].split("/")[0]
    if "/user/" in url:
        return url.split("/user/")[1].split("/")[0]
    if "/@" in url:
        return url.split("/@")[1].split("/")[0]
    return None

# ================== INTERFAZ ==================

root = tk.Tk()
root.title("🎵 Descargador YouTube → MP3 con cola")
root.geometry("1000x600")
root.resizable(False, False)

style = ttk.Style()
style.theme_use("clam")

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
style.map("Accent.TButton", background=[("active", "#005A9E")])
style.configure(
    "Danger.TButton",
    font=("Segoe UI", 10, "bold"),
    foreground="white",
    background="#D83B01",
    padding=6
)
style.map("Danger.TButton", background=[("active", "#A4262C")])

ttk.Label(
    root,
    text="Descargador de Canales / Playlists YouTube → MP3 (con cola de URLs)",
    style="Title.TLabel"
).pack(pady=8)

main = ttk.Frame(root, padding="10 5 10 10")
main.pack(fill="both", expand=True)

# ---- Panel izquierdo: ajustes ----
left = ttk.Frame(main)
left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
main.columnconfigure(0, weight=1)
main.columnconfigure(1, weight=1)

# 1. URL
ttk.Label(left, text="1. URL a añadir a la cola:").grid(row=0, column=0, sticky="w", pady=3)
entry_url = ttk.Entry(left, width=60)
entry_url.grid(row=1, column=0, pady=3, sticky="we")

# Botón añadir a cola
btn_add_queue = ttk.Button(left, text="➕ Añadir URL a la cola")
btn_add_queue.grid(row=1, column=1, padx=5)

# 2. Carpeta descargas
ttk.Label(left, text="2. Carpeta de descargas:").grid(row=2, column=0, sticky="w", pady=3)
frame_ruta = ttk.Frame(left)
frame_ruta.grid(row=3, column=0, columnspan=2, pady=3, sticky="we")
entry_ruta = ttk.Entry(frame_ruta, width=50)
entry_ruta.pack(side="left", fill="x", expand=True)

def seleccionar_carpeta_descargas():
    carpeta = filedialog.askdirectory(title="Elige carpeta para guardar los MP3")
    if carpeta:
        entry_ruta.delete(0, tk.END)
        entry_ruta.insert(0, carpeta)

ttk.Button(frame_ruta, text="📁 Buscar", command=seleccionar_carpeta_descargas)\
    .pack(side="left", padx=5)

# 3. Carpeta FFmpeg
ttk.Label(left, text="3. Carpeta de FFmpeg (opcional):").grid(row=4, column=0, sticky="w", pady=3)
frame_ffmpeg = ttk.Frame(left)
frame_ffmpeg.grid(row=5, column=0, columnspan=2, pady=3, sticky="we")
entry_ffmpeg = ttk.Entry(frame_ffmpeg, width=50)
entry_ffmpeg.pack(side="left", fill="x", expand=True)

def seleccionar_ffmpeg():
    carpeta = filedialog.askdirectory(
        title="Selecciona carpeta con ffmpeg.exe y ffprobe.exe"
    )
    if carpeta:
        entry_ffmpeg.delete(0, tk.END)
        entry_ffmpeg.insert(0, carpeta)

ttk.Button(frame_ffmpeg, text="📁 Buscar ffmpeg", command=seleccionar_ffmpeg)\
    .pack(side="left", padx=5)

# 4. Calidad
ttk.Label(left, text="4. Calidad de audio (kbps):").grid(row=6, column=0, sticky="w", pady=3)
calidad_var = tk.StringVar(value="320")
calidad_cb = ttk.Combobox(
    left,
    textvariable=calidad_var,
    values=["128", "192", "256", "320"],
    width=8,
    state="readonly"
)
calidad_cb.grid(row=7, column=0, pady=3, sticky="w")

# Progreso
ttk.Label(left, text="Progreso descarga actual:").grid(row=8, column=0, sticky="w", pady=(10, 3))
progress = ttk.Progressbar(left, orient="horizontal", mode="determinate", length=400)
progress.grid(row=9, column=0, columnspan=2, pady=3, sticky="we")

# Botones control
btn_frame = ttk.Frame(left)
btn_frame.grid(row=10, column=0, columnspan=2, pady=12, sticky="w")

btn_iniciar = ttk.Button(btn_frame, text="▶ Empezar cola", style="Accent.TButton")
btn_iniciar.pack(side="left", padx=4)

btn_detener = ttk.Button(btn_frame, text="⏹ Detener todo", style="Danger.TButton", state="disabled")
btn_detener.pack(side="left", padx=4)

ttk.Button(btn_frame, text="Salir", command=root.quit).pack(side="left", padx=4)

# ---- Panel derecho: cola + log ----
right = ttk.Frame(main)
right.grid(row=0, column=1, sticky="nsew")
main.rowconfigure(0, weight=1)

# Cola de URLs
ttk.Label(right, text="Cola de playlists / canales / vídeos:").grid(row=0, column=0, sticky="w")
listbox_queue = tk.Listbox(right, height=10, width=60)
listbox_queue.grid(row=1, column=0, sticky="we", pady=3)
scroll_q = ttk.Scrollbar(right, orient="vertical", command=listbox_queue.yview)
scroll_q.grid(row=1, column=1, sticky="ns", pady=3)
listbox_queue.configure(yscrollcommand=scroll_q.set)

# Log
ttk.Label(right, text="Log de operaciones:").grid(row=2, column=0, sticky="w", pady=(10, 3))
text_log = tk.Text(right, width=70, height=15, state="disabled", bg="#f8f8f8", relief="solid", bd=1)
text_log.grid(row=3, column=0, pady=3, sticky="we")
scroll_log = ttk.Scrollbar(right, orient="vertical", command=text_log.yview)
scroll_log.grid(row=3, column=1, sticky="ns", pady=3)
text_log.configure(yscrollcommand=scroll_log.set)

def log(msg):
    text_log.configure(state="normal")
    text_log.insert(tk.END, msg + "\n")
    text_log.see(tk.END)
    text_log.configure(state="disabled")

# Ruta por defecto
default_path = os.path.join(os.path.expanduser("~"), "Audios_YouTube")
entry_ruta.insert(0, default_path)

# ================== COLA Y ESTADO ==================

url_queue = []               # cola de URLs
descarga_activa = threading.Event()
descarga_cancelada = threading.Event()

def add_to_queue():
    url = entry_url.get().strip()
    if not url:
        messagebox.showwarning("Aviso", "Pega primero una URL.")
        return
    url_queue.append(url)
    listbox_queue.insert(tk.END, url)
    entry_url.delete(0, tk.END)
    log(f"➕ Añadida a la cola: {url}")

btn_add_queue.config(command=add_to_queue)

# ================== DESCARGA ==================

def progreso_hook(d):
    if descarga_cancelada.is_set():
        raise yt_dlp.utils.DownloadError("Descarga cancelada por el usuario")

    if d.get("status") == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        if total:
            porcentaje = d["downloaded_bytes"] / total * 100
            speed = d.get("speed") or 0
            eta = d.get("eta") or 0
            root.after(0, lambda: progress.configure(value=porcentaje))
            root.after(0, lambda: log(
                f"⬇ {os.path.basename(d['filename'])} "
                f"{porcentaje:5.1f}%  {speed/1024:6.1f} KiB/s  ETA {eta:4d}s"
            ))
    elif d.get("status") == "finished":
        root.after(0, lambda: log(f"✅ Convertido a MP3: {os.path.basename(d['filename'])}"))

def construir_opts(carpeta, carpeta_ffmpeg, calidad):
    os.makedirs(carpeta, exist_ok=True)
    archive_file = os.path.join(carpeta, "descargados.txt")

    ffmpeg_location = None
    if carpeta_ffmpeg:
        ffmpeg_location = buscar_ffmpeg(carpeta_ffmpeg)
        if not ffmpeg_location:
            messagebox.showwarning(
                "Advertencia",
                "No se encontró ffmpeg.exe/ffprobe.exe en la carpeta indicada."
            )
    if not ffmpeg_location and ffmpeg_en_path():
        ffmpeg_location = None

    opts = {
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
        opts["ffmpeg_location"] = ffmpeg_location
    return opts

def normalizar_url(url):
    if "youtube.com" in url and ("/channel/" in url or "/user/" in url or "/@" in url):
        canal_id = obtener_id_canal(url)
        if canal_id:
            nueva = f"https://www.youtube.com/channel/{canal_id}/videos"
            log(f"🔎 Detectado canal → usando URL: {nueva}")
            return nueva
    return url

def procesar_cola():
    carpeta = entry_ruta.get().strip()
    carpeta_ffmpeg = entry_ffmpeg.get().strip()
    calidad = calidad_var.get()

    if not carpeta:
        messagebox.showerror("Error", "Debes elegir la carpeta de descargas.")
        descarga_activa.clear()
        return

    ydl_opts = construir_opts(carpeta, carpeta_ffmpeg, calidad)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            while url_queue and not descarga_cancelada.is_set():
                url_actual = url_queue.pop(0)
                root.after(0, lambda: listbox_queue.delete(0))  # quita primera de la lista
                url_final = normalizar_url(url_actual)
                log(f"▶ Descargando: {url_final}")
                progress.configure(value=0)
                try:
                    ydl.download([url_final])
                    log("✅ Lista/URL terminada.\n")
                except yt_dlp.utils.DownloadError as e:
                    if "cancelada" in str(e):
                        log("⏹ Descarga cancelada por el usuario.")
                        break
                    else:
                        log(f"❌ Error en URL {url_final}: {e}")
                except Exception as e:
                    log(f"❌ Error inesperado en URL {url_final}: {e}")
    finally:
        root.after(0, lambda: btn_iniciar.config(state="normal"))
        root.after(0, lambda: btn_detener.config(state="disabled"))
        root.after(0, lambda: progress.configure(value=0))
        descarga_activa.clear()
        if not descarga_cancelada.is_set():
            log("🏁 Cola finalizada.")

def iniciar_cola():
    if not url_queue:
        messagebox.showwarning("Aviso", "No hay ninguna URL en la cola.")
        return
    if descarga_activa.is_set():
        messagebox.showinfo("Info", "Ya se está procesando la cola.")
        return

    descarga_activa.set()
    descarga_cancelada.clear()
    btn_iniciar.config(state="disabled")
    btn_detener.config(state="normal")
    log("🚀 Empezando a procesar la cola...")

    hilo = threading.Thread(target=procesar_cola, daemon=True)
    hilo.start()

def detener_todo():
    if descarga_activa.is_set():
        descarga_cancelada.set()
        log("⏹ Solicitando cancelación de la cola...")

btn_iniciar.config(command=iniciar_cola)
btn_detener.config(command=detener_todo)

root.mainloop()
