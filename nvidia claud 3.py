import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import os
import sys
import threading
import subprocess

# ================== FUNCIONES AUXILIARES ==================

def get_app_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def buscar_ffmpeg(carpeta):
    ffmpeg_path = os.path.join(carpeta, "ffmpeg.exe")
    ffprobe_path = os.path.join(carpeta, "ffprobe.exe")
    if os.path.isfile(ffmpeg_path) and os.path.isfile(ffprobe_path):
        return carpeta
    return None


def buscar_ffmpeg_en_carpetas(carpeta):
    if not carpeta:
        return None
    posibles = [
        carpeta,
        os.path.join(carpeta, "ffmpeg"),
        os.path.join(carpeta, "ffmpeg", "bin"),
        os.path.join(carpeta, "bin")
    ]
    for carpeta_cand in posibles:
        if carpeta_cand and os.path.isdir(carpeta_cand):
            resultado = buscar_ffmpeg(carpeta_cand)
            if resultado:
                return resultado
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

# ================== INICIO: detectar DPI y escalar ==================

root = tk.Tk()
root.withdraw()  # ocultar mientras calculamos escala

# Leer DPI real del sistema para respetar configuración de accesibilidad del usuario
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

dpi = root.winfo_fpixels("1i")         # píxeles por pulgada reales
ESCALA = max(1.0, dpi / 96.0)          # 96 DPI = 100%, 120 DPI = 125%, 144 = 150%…

def e(px):
    """Escala un valor de píxeles al DPI real del usuario."""
    return int(px * ESCALA)

# Fuentes escaladas
F_NORMAL   = ("Segoe UI", int(10 * ESCALA))
F_BOLD     = ("Segoe UI", int(10 * ESCALA), "bold")
F_TITLE    = ("Segoe UI", int(16 * ESCALA), "bold")
F_BUTTON   = ("Segoe UI", int(10 * ESCALA), "bold")
F_LOG      = ("Consolas",  int(9  * ESCALA))

# ================== VENTANA PRINCIPAL ==================

root.title("🎵 YouTube → MP3  |  Cola de descargas")
root.geometry(f"{e(1020)}x{e(650)}")
root.minsize(e(800), e(500))
root.deiconify()  # mostrar ahora que ya está configurada

# Maximizar/minimizar con botones nativos (resizable)
root.resizable(True, True)

# ================== ESTILOS ==================

style = ttk.Style()
style.theme_use("clam")

PAD = e(6)

style.configure("TFrame",   background="#F3F3F3")
style.configure("TLabel",   background="#F3F3F3", font=F_NORMAL)
style.configure("TEntry",   font=F_NORMAL, padding=PAD)
style.configure("TCombobox", font=F_NORMAL)
style.configure("TButton",  font=F_BUTTON, padding=PAD)

style.configure("Title.TLabel",
                font=F_TITLE,
                background="#0078D7",
                foreground="white",
                padding=e(12))

style.configure("Accent.TButton",
                font=F_BUTTON,
                foreground="white",
                background="#0078D7",
                padding=e(8))
style.map("Accent.TButton", background=[("active", "#005A9E"), ("disabled", "#AAAAAA")])

style.configure("Danger.TButton",
                font=F_BUTTON,
                foreground="white",
                background="#D83B01",
                padding=e(8))
style.map("Danger.TButton", background=[("active", "#A4262C"), ("disabled", "#AAAAAA")])

style.configure("Green.TButton",
                font=F_BUTTON,
                foreground="white",
                background="#107C10",
                padding=e(8))
style.map("Green.TButton", background=[("active", "#0A5A0A")])

style.configure("TProgressbar",
                troughcolor="#D0D0D0",
                background="#0078D7",
                thickness=e(18))

# ================== LAYOUT PRINCIPAL ==================

# Barra de título de color
ttk.Label(root, text="🎵  Descargador YouTube → MP3  |  Cola de playlists",
          style="Title.TLabel").pack(fill="x")

paned = ttk.PanedWindow(root, orient="horizontal")
paned.pack(fill="both", expand=True, padx=e(10), pady=e(10))

left_frame  = ttk.Frame(paned, padding=e(10))
right_frame = ttk.Frame(paned, padding=e(10))
paned.add(left_frame,  weight=1)
paned.add(right_frame, weight=1)

# ================== PANEL IZQUIERDO: controles ==================

left_frame.columnconfigure(1, weight=1)

def label(parent, text, row, col=0, pady=3, sticky="w", columnspan=1):
    ttk.Label(parent, text=text).grid(
        row=row, column=col, sticky=sticky,
        pady=pady, padx=(0, e(8)), columnspan=columnspan
    )

# --- URL ---
label(left_frame, "URL del canal / playlist / vídeo:", 0, columnspan=2, pady=(0, 3))

frame_url = ttk.Frame(left_frame)
frame_url.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, e(8)))
frame_url.columnconfigure(0, weight=1)

entry_url = ttk.Entry(frame_url, font=F_NORMAL)
entry_url.grid(row=0, column=0, sticky="we", padx=(0, e(6)))

def menu_contextual_url(event):
    """Menú botón derecho: copiar/pegar/cortar para el campo URL."""
    menu = tk.Menu(root, tearoff=0, font=F_NORMAL)
    menu.add_command(label="✂ Cortar",   command=lambda: entry_url.event_generate("<<Cut>>"))
    menu.add_command(label="📋 Copiar",  command=lambda: entry_url.event_generate("<<Copy>>"))
    menu.add_command(label="📌 Pegar",   command=lambda: entry_url.event_generate("<<Paste>>"))
    menu.add_separator()
    menu.add_command(label="🗑 Limpiar", command=lambda: entry_url.delete(0, tk.END))
    menu.tk_popup(event.x_root, event.y_root)

entry_url.bind("<Button-3>", menu_contextual_url)

btn_add_queue = ttk.Button(frame_url, text="➕ Añadir a cola", style="Green.TButton")
btn_add_queue.grid(row=0, column=1)

# --- Carpeta descargas ---
label(left_frame, "Carpeta de descargas:", 2, columnspan=2)
frame_ruta = ttk.Frame(left_frame)
frame_ruta.grid(row=3, column=0, columnspan=2, sticky="we", pady=(0, e(8)))
frame_ruta.columnconfigure(0, weight=1)
entry_ruta = ttk.Entry(frame_ruta, font=F_NORMAL)
entry_ruta.grid(row=0, column=0, sticky="we", padx=(0, e(6)))

def menu_contextual_ruta(event):
    menu = tk.Menu(root, tearoff=0, font=F_NORMAL)
    menu.add_command(label="📋 Copiar",  command=lambda: entry_ruta.event_generate("<<Copy>>"))
    menu.add_command(label="📌 Pegar",   command=lambda: entry_ruta.event_generate("<<Paste>>"))
    menu.add_separator()
    menu.add_command(label="🗑 Limpiar", command=lambda: entry_ruta.delete(0, tk.END))
    menu.tk_popup(event.x_root, event.y_root)

entry_ruta.bind("<Button-3>", menu_contextual_ruta)

def seleccionar_carpeta_descargas():
    carpeta = filedialog.askdirectory(title="Elige carpeta para guardar los MP3")
    if carpeta:
        entry_ruta.delete(0, tk.END)
        entry_ruta.insert(0, carpeta)

ttk.Button(frame_ruta, text="📁 Buscar", command=seleccionar_carpeta_descargas)\
    .grid(row=0, column=1)

# --- Carpeta FFmpeg ---
label(left_frame, "Carpeta de FFmpeg (opcional):", 4, columnspan=2)
frame_ffmpeg = ttk.Frame(left_frame)
frame_ffmpeg.grid(row=5, column=0, columnspan=2, sticky="we", pady=(0, e(8)))
frame_ffmpeg.columnconfigure(0, weight=1)
entry_ffmpeg = ttk.Entry(frame_ffmpeg, font=F_NORMAL)
entry_ffmpeg.grid(row=0, column=0, sticky="we", padx=(0, e(6)))

def menu_contextual_ffmpeg(event):
    menu = tk.Menu(root, tearoff=0, font=F_NORMAL)
    menu.add_command(label="📋 Copiar",  command=lambda: entry_ffmpeg.event_generate("<<Copy>>"))
    menu.add_command(label="📌 Pegar",   command=lambda: entry_ffmpeg.event_generate("<<Paste>>"))
    menu.add_separator()
    menu.add_command(label="🗑 Limpiar", command=lambda: entry_ffmpeg.delete(0, tk.END))
    menu.tk_popup(event.x_root, event.y_root)

entry_ffmpeg.bind("<Button-3>", menu_contextual_ffmpeg)

def seleccionar_ffmpeg():
    carpeta = filedialog.askdirectory(
        title="Selecciona la carpeta con ffmpeg.exe y ffprobe.exe"
    )
    if carpeta:
        entry_ffmpeg.delete(0, tk.END)
        entry_ffmpeg.insert(0, carpeta)

ttk.Button(frame_ffmpeg, text="📁 Buscar ffmpeg", command=seleccionar_ffmpeg)\
    .grid(row=0, column=1)

# --- Calidad ---
label(left_frame, "Calidad de audio (kbps):", 6, columnspan=2)
calidad_var = tk.StringVar(value="320")
calidad_cb = ttk.Combobox(
    left_frame,
    textvariable=calidad_var,
    values=["128", "192", "256", "320"],
    width=8,
    state="readonly",
    font=F_NORMAL
)
calidad_cb.grid(row=7, column=0, columnspan=2, sticky="w", pady=(0, e(10)))

# --- Progreso ---
label(left_frame, "Progreso descarga actual:", 8, columnspan=2)
progress = ttk.Progressbar(
    left_frame, orient="horizontal",
    mode="determinate", style="TProgressbar"
)
progress.grid(row=9, column=0, columnspan=2, sticky="we", pady=(0, e(6)))

# Etiqueta de estado
lbl_estado = ttk.Label(left_frame, text="En espera.", foreground="#555555")
lbl_estado.grid(row=10, column=0, columnspan=2, sticky="w", pady=(0, e(10)))

def set_estado(msg, color="#555555"):
    root.after(0, lambda: lbl_estado.config(text=msg, foreground=color))

# --- Botones de control ---
btn_frame = ttk.Frame(left_frame)
btn_frame.grid(row=11, column=0, columnspan=2, sticky="w", pady=(0, e(6)))

btn_iniciar = ttk.Button(btn_frame, text="▶  Empezar cola", style="Accent.TButton")
btn_iniciar.pack(side="left", padx=(0, e(6)))

btn_detener = ttk.Button(btn_frame, text="⏹  Detener", style="Danger.TButton", state="disabled")
btn_detener.pack(side="left", padx=(0, e(6)))

ttk.Button(btn_frame, text="Salir", command=root.quit).pack(side="left")

# ================== PANEL DERECHO: cola + log ==================

right_frame.columnconfigure(0, weight=1)
right_frame.rowconfigure(1, weight=1)
right_frame.rowconfigure(3, weight=2)

# --- Cola ---
ttk.Label(right_frame, text="📋  Cola de URLs pendientes:").grid(
    row=0, column=0, sticky="w", pady=(0, e(4))
)

frame_queue = ttk.Frame(right_frame)
frame_queue.grid(row=1, column=0, sticky="nswe")
frame_queue.columnconfigure(0, weight=1)
frame_queue.rowconfigure(0, weight=1)

listbox_queue = tk.Listbox(
    frame_queue,
    font=F_NORMAL,
    selectmode=tk.SINGLE,
    bg="#FFFFFF",
    relief="solid",
    bd=1,
    activestyle="dotbox"
)
listbox_queue.grid(row=0, column=0, sticky="nswe")
scroll_q = ttk.Scrollbar(frame_queue, orient="vertical", command=listbox_queue.yview)
scroll_q.grid(row=0, column=1, sticky="ns")
listbox_queue.configure(yscrollcommand=scroll_q.set)

# Menú botón derecho en la cola
def menu_contextual_cola(event):
    idx = listbox_queue.nearest(event.y)
    if idx < 0:
        return
    listbox_queue.selection_clear(0, tk.END)
    listbox_queue.selection_set(idx)
    menu = tk.Menu(root, tearoff=0, font=F_NORMAL)
    menu.add_command(label="🗑 Eliminar URL seleccionada",
                     command=lambda: eliminar_url_cola())
    menu.add_command(label="🗑 Limpiar toda la cola",
                     command=lambda: limpiar_cola())
    menu.tk_popup(event.x_root, event.y_root)

listbox_queue.bind("<Button-3>", menu_contextual_cola)

def eliminar_url_cola():
    sel = listbox_queue.curselection()
    if sel:
        idx = sel[0]
        listbox_queue.delete(idx)
        if idx < len(url_queue):
            del url_queue[idx]

def limpiar_cola():
    listbox_queue.delete(0, tk.END)
    url_queue.clear()

# --- Log ---
ttk.Label(right_frame, text="📝  Log de operaciones:").grid(
    row=2, column=0, sticky="w", pady=(e(10), e(4))
)

frame_log = ttk.Frame(right_frame)
frame_log.grid(row=3, column=0, sticky="nswe")
frame_log.columnconfigure(0, weight=1)
frame_log.rowconfigure(0, weight=1)

text_log = tk.Text(
    frame_log,
    font=F_LOG,
    state="disabled",
    bg="#1E1E1E",
    fg="#D4D4D4",
    relief="solid",
    bd=1,
    wrap="word"
)
text_log.grid(row=0, column=0, sticky="nswe")
scroll_log = ttk.Scrollbar(frame_log, orient="vertical", command=text_log.yview)
scroll_log.grid(row=0, column=1, sticky="ns")
text_log.configure(yscrollcommand=scroll_log.set)

# Colores en el log
text_log.tag_configure("ok",      foreground="#6EC06E")
text_log.tag_configure("error",   foreground="#F44747")
text_log.tag_configure("info",    foreground="#9CDCFE")
text_log.tag_configure("warn",    foreground="#CE9178")
text_log.tag_configure("progreso",foreground="#888888")

# Menú botón derecho en el log
def menu_contextual_log(event):
    menu = tk.Menu(root, tearoff=0, font=F_NORMAL)
    menu.add_command(label="📋 Copiar todo el log",
                     command=lambda: root.clipboard_clear() or
                                     root.clipboard_append(text_log.get("1.0", tk.END)))
    menu.add_separator()
    menu.add_command(label="🗑 Limpiar log",
                     command=lambda: [text_log.configure(state="normal"),
                                      text_log.delete("1.0", tk.END),
                                      text_log.configure(state="disabled")])
    menu.tk_popup(event.x_root, event.y_root)

text_log.bind("<Button-3>", menu_contextual_log)

def log(msg, tag="info"):
    def _write():
        text_log.configure(state="normal")
        text_log.insert(tk.END, msg + "\n", tag)
        text_log.see(tk.END)
        text_log.configure(state="disabled")
    root.after(0, _write)

# Ruta por defecto
default_path = os.path.join(os.path.expanduser("~"), "Audios_YouTube")
entry_ruta.insert(0, default_path)

# ================== COLA Y LÓGICA DE DESCARGA ==================

url_queue = []
descarga_activa   = threading.Event()
descarga_cancelada = threading.Event()

def add_to_queue():
    url = entry_url.get().strip()
    if not url:
        messagebox.showwarning("Aviso", "Pega primero una URL.")
        return
    url_queue.append(url)
    listbox_queue.insert(tk.END, url)
    entry_url.delete(0, tk.END)
    log(f"➕ Añadida a la cola: {url}", "info")
    # Si el hilo no está corriendo, arrancar automáticamente
    if not descarga_activa.is_set():
        iniciar_cola()

btn_add_queue.config(command=add_to_queue)
# También añadir con Enter desde el campo URL
entry_url.bind("<Return>", lambda e: add_to_queue())

def progreso_hook(d):
    if descarga_cancelada.is_set():
        raise yt_dlp.utils.DownloadError("Descarga cancelada por el usuario")

    if d.get("status") == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        if total:
            pct   = d["downloaded_bytes"] / total * 100
            speed = d.get("speed") or 0
            eta   = d.get("eta") or 0
            root.after(0, lambda: progress.configure(value=pct))
            set_estado(
                f"{os.path.basename(d['filename'])} — "
                f"{pct:5.1f}%  {speed/1024:5.1f} KiB/s  ETA {eta}s",
                "#0078D7"
            )
            log(
                f"⬇ {os.path.basename(d['filename'])} "
                f"{pct:5.1f}%  {speed/1024:5.1f} KiB/s  ETA {eta}s",
                "progreso"
            )
    elif d.get("status") == "finished":
        nombre = os.path.basename(d["filename"])
        log(f"✅ Convertido: {nombre}", "ok")

def construir_opts(carpeta, carpeta_ffmpeg, calidad):
    os.makedirs(carpeta, exist_ok=True)
    archive_file = os.path.join(carpeta, "descargados.txt")

    ffmpeg_location = None
    if carpeta_ffmpeg:
        ffmpeg_location = buscar_ffmpeg_en_carpetas(carpeta_ffmpeg)
        if not ffmpeg_location:
            messagebox.showwarning(
                "Advertencia",
                "No se encontró ffmpeg.exe/ffprobe.exe en la carpeta indicada."
            )

    if not ffmpeg_location:
        ffmpeg_location = buscar_ffmpeg_en_carpetas(get_app_base_path())

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
    if "youtube.com" in url and (
        "/channel/" in url or "/user/" in url or "/@" in url
    ):
        canal_id = obtener_id_canal(url)
        if canal_id:
            nueva = f"https://www.youtube.com/channel/{canal_id}/videos"
            log(f"🔎 Canal detectado → {nueva}", "warn")
            return nueva
    return url

def procesar_cola():
    carpeta       = entry_ruta.get().strip()
    carpeta_ffmpeg = entry_ffmpeg.get().strip()
    calidad       = calidad_var.get()

    if not carpeta:
        messagebox.showerror("Error", "Debes elegir la carpeta de descargas.")
        descarga_activa.clear()
        return

    ydl_opts = construir_opts(carpeta, carpeta_ffmpeg, calidad)
    total_completadas = 0

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            while url_queue and not descarga_cancelada.is_set():
                url_actual = url_queue.pop(0)
                root.after(0, lambda: listbox_queue.delete(0))
                url_final = normalizar_url(url_actual)
                log(f"\n▶ Iniciando: {url_final}", "info")
                set_estado(f"Descargando: {url_final[:60]}...", "#0078D7")
                root.after(0, lambda: progress.configure(value=0))
                try:
                    ydl.download([url_final])
                    total_completadas += 1
                    log(f"✅ URL finalizada: {url_final}", "ok")
                except yt_dlp.utils.DownloadError as e:
                    if "cancelada" in str(e):
                        log("⏹ Cancelado por el usuario.", "warn")
                        break
                    log(f"❌ Error en {url_final}: {e}", "error")
                except Exception as e:
                    log(f"❌ Error inesperado en {url_final}: {e}", "error")
    finally:
        root.after(0, lambda: btn_iniciar.config(state="normal"))
        root.after(0, lambda: btn_detener.config(state="disabled"))
        root.after(0, lambda: progress.configure(value=0))
        descarga_activa.clear()
        descarga_cancelada.clear()
        if total_completadas > 0:
            set_estado(
                f"🏁 Cola finalizada. {total_completadas} lista(s) descargadas.",
                "#107C10"
            )
            log(
                f"\n🏁 Todo listo. {total_completadas} lista(s)/canal(es) descargados.",
                "ok"
            )
        else:
            set_estado("Cancelado.", "#D83B01")

def iniciar_cola():
    if not url_queue:
        return
    if descarga_activa.is_set():
        return
    descarga_activa.set()
    descarga_cancelada.clear()
    btn_iniciar.config(state="disabled")
    btn_detener.config(state="normal")
    log("🚀 Procesando cola...", "info")
    threading.Thread(target=procesar_cola, daemon=True).start()

def detener_todo():
    if descarga_activa.is_set():
        descarga_cancelada.set()
        log("⏹ Solicitando cancelación...", "warn")
        set_estado("Cancelando...", "#D83B01")

btn_iniciar.config(command=iniciar_cola)
btn_detener.config(command=detener_todo)

root.mainloop()
