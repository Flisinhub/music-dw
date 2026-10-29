import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import os
import sys
import threading
import subprocess
import time
from datetime import datetime

# ================== FUNCIONES AUXILIARES ==================

def get_app_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def obtener_ruta_node():
    for carpeta in (getattr(sys, "_MEIPASS", None), get_app_base_path()):
        if carpeta:
            node_path = os.path.join(carpeta, "node.exe")
            if os.path.isfile(node_path):
                return node_path
    return None


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


def es_url_valida(url):
    if not url:
        return False
    url_lower = url.lower()
    return "youtube.com" in url_lower or "youtu.be" in url_lower


def es_playlist_url(url):
    if not url:
        return False
    url_lower = url.lower()
    return "list=" in url_lower or "/playlist" in url_lower


def registrar_error_archivo(mensaje):
    try:
        ruta_log = os.path.join(get_app_base_path(), "yt_dlp_errors.log")
        with open(ruta_log, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} - {mensaje}\n")
    except Exception:
        pass

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

def obtener_factor_texto_windows():
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Accessibility"
        ) as clave:
            valor, _ = winreg.QueryValueEx(clave, "TextScaleFactor")
        return max(1.0, min(float(valor) / 100.0, 2.25))
    except (ImportError, OSError, TypeError, ValueError):
        return 1.0

dpi = root.winfo_fpixels("1i")         # píxeles por pulgada reales
FACTOR_TEXTO = obtener_factor_texto_windows()
ESCALA_DPI = max(1.0, dpi / 96.0)
ESCALA = ESCALA_DPI

def e(px):
    """Escala un valor de píxeles al DPI real del usuario."""
    return int(px * ESCALA)

# Fuentes escaladas
ESCALA_FUENTE = ESCALA_DPI * FACTOR_TEXTO
F_NORMAL   = ("Segoe UI", int(10 * ESCALA_FUENTE))
F_BOLD     = ("Segoe UI", int(10 * ESCALA_FUENTE), "bold")
F_TITLE    = ("Segoe UI", int(16 * ESCALA_FUENTE), "bold")
F_BUTTON   = ("Segoe UI", int(10 * ESCALA_FUENTE), "bold")
F_LOG      = ("Consolas",  int(10 * ESCALA_FUENTE))

# ================== VENTANA PRINCIPAL ==================

root.title("🎵 YouTube → MP3 / MP4  |  Cola de descargas")
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
style.configure("Treeview", font=F_NORMAL, rowheight=e(28))
style.configure("Treeview.Heading", font=F_BOLD)

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
entry_url.grid(row=0, column=0, columnspan=3, sticky="we", pady=(0, e(6)))

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
btn_add_queue.grid(row=1, column=0, sticky="w", padx=(0, e(6)))

btn_load_txt = ttk.Button(frame_url, text="📄 Cargar .txt", style="Accent.TButton")
btn_load_txt.grid(row=1, column=1, sticky="w")

def cargar_urls_desde_archivo():
    """Carga múltiples URLs desde un archivo .txt (una URL por línea)."""
    global ultima_carpeta_destino
    archivo = filedialog.askopenfilename(
        title="Selecciona archivo .txt con URLs",
        filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
    )
    if not archivo:
        return

    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")
        return

    urls_validas = []
    urls_invalidas = []

    for linea in lineas:
        url = linea.strip()
        if not url or url.startswith('#'):  # Ignorar líneas vacías y comentarios
            continue
        if es_url_valida(url):
            urls_validas.append(url)
        else:
            urls_invalidas.append(url)

    if not urls_validas:
        if urls_invalidas:
            messagebox.showwarning("Sin URLs válidas",
                f"No se encontraron URLs válidas de YouTube en el archivo.\n"
                f"Se encontraron {len(urls_invalidas)} líneas inválidas.")
        else:
            messagebox.showwarning("Archivo vacío", "El archivo no contiene ninguna URL.")
        return

    # Seleccionar carpeta destino común para las URLs cargadas
    carpeta_item = filedialog.askdirectory(
        title="Selecciona carpeta destino para todas las URLs",
        initialdir=ultima_carpeta_destino
    )
    if not carpeta_item:
        return
    ultima_carpeta_destino = carpeta_item

    # Agregar todas las URLs a la cola
    urls_duplicadas = 0
    for url in urls_validas:
        if any(item["url"] == url for item in url_queue):
            urls_duplicadas += 1
            continue
        url_queue.append({"url": url, "folder": carpeta_item})
        queue_tree.insert("", tk.END, values=(url, carpeta_item))
        log(f"➕ Añadida desde archivo: {url} → {carpeta_item}", "info")

    # Resumen
    resumen = f"✅ Se cargaron {len(urls_validas)} URL(s)"
    if urls_duplicadas > 0:
        resumen += f"\n⚠️ {urls_duplicadas} URL(s) ya estaban en la cola"
    if urls_invalidas:
        resumen += f"\n❌ {len(urls_invalidas)} línea(s) inválida(s) ignorada(s)"

    messagebox.showinfo("Carga completada", resumen)
    log(f"📂 Archivo cargado: {len(urls_validas)} URL(s) procesadas", "ok")

btn_load_txt.config(command=cargar_urls_desde_archivo)

# --- Carpeta FFmpeg ---
label(left_frame, "Carpeta de FFmpeg (opcional):", 2, columnspan=2)
frame_ffmpeg = ttk.Frame(left_frame)
frame_ffmpeg.grid(row=3, column=0, columnspan=2, sticky="we", pady=(0, e(8)))
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

# --- Cookies YouTube ---
label(left_frame, "Cookies YouTube (usa navegador o archivo de cookies):", 4, columnspan=2)
frame_cookies = ttk.Frame(left_frame)
frame_cookies.grid(row=5, column=0, columnspan=2, sticky="we", pady=(0, e(8)))
frame_cookies.columnconfigure(0, weight=1)
cookies_config_var = tk.StringVar(value="")

cookies_browser_var = tk.StringVar(value="firefox")
cookies_browser_cb = ttk.Combobox(
    frame_cookies,
    textvariable=cookies_browser_var,
    values=["chrome", "edge", "firefox", "opera", "brave", "vivaldi"],
    width=12,
    state="readonly",
    font=F_NORMAL
)
cookies_browser_cb.grid(row=0, column=0, padx=(0, e(6)))

def seleccionar_cookies():
    archivo = filedialog.askopenfilename(
        title="Selecciona archivo de cookies de YouTube",
        filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
    )
    if archivo:
        cookies_config_var.set(archivo)

def configurar_cookies_navegador():
    navegador_seleccionado = cookies_browser_var.get()
    try:
        import yt_dlp
        ydl = yt_dlp.YoutubeDL({"cookiesfrombrowser": (navegador_seleccionado,)})
        cookies_config_var.set(f"browser:{navegador_seleccionado}")
        log(f"🍪 Configurado para usar cookies de {navegador_seleccionado}", "info")
        messagebox.showinfo("Cookies", f"Cookies de {navegador_seleccionado} configuradas correctamente.")
    except Exception as e:
        mensaje = str(e)
        log(f"❌ Error obteniendo cookies: {mensaje}", "error")
        if "Could not copy Chrome cookie database" in mensaje or "Permission denied" in mensaje:
            messagebox.showerror(
                "Error cookies navegador",
                "No se pudo copiar la base de datos de cookies.\n\n" \
                "Cierra completamente el navegador seleccionado y vuelve a intentar.\n" \
                "Si es Chrome, puedes abrirlo con la bandera:\n" \
                "--disable-features=LockProfileCookieDatabase\n\n" \
                "Si sigue fallando, exporta un archivo de cookies desde el navegador e introdúcelo con el botón '📄 Archivo'."
            )
        elif "Failed to decrypt with DPAPI" in mensaje:
            messagebox.showerror(
                "Error DPAPI cookies",
                "No se pudieron descifrar las cookies del navegador (issue 10927 de yt-dlp).\n\n" \
                "Este es un problema conocido de Chrome en Windows.\n" \
                "Prueba uno de estos métodos:\n" \
                "• Usa Firefox o Linux para extraer cookies.\n" \
                "• Exporta cookies con una extensión de Chrome y usa '📄 Archivo'.\n" \
                "• Si necesitas seguir con Chrome, usa el mismo usuario de Windows y cierra Chrome antes de extraer."
            )
        else:
            messagebox.showerror(
                "Error cookies navegador",
                f"No se pudieron obtener las cookies de {navegador_seleccionado}:\n\n{mensaje}\n\n" \
                "Asegúrate de que el navegador esté instalado, logueado en YouTube y cerrado antes de intentar de nuevo."
            )

def autoconfigurar_cookies_firefox():
    """Extrae automáticamente las cookies de Firefox al iniciar."""
    try:
        import yt_dlp
        ydl = yt_dlp.YoutubeDL({"cookiesfrombrowser": ("firefox",)})
        cookies_config_var.set("browser:firefox")
        log("🍪 Cookies de Firefox configuradas automáticamente al iniciar", "ok")
        return True
    except Exception as e:
        log(f"⚠️ No se pudieron extraer cookies de Firefox: {str(e)}", "warning")
        return False

ttk.Button(frame_cookies, text="📄 Archivo", command=seleccionar_cookies)\
    .grid(row=0, column=1, padx=(0, e(6)))
ttk.Button(frame_cookies, text="🌐 Extraer", command=configurar_cookies_navegador)\
    .grid(row=0, column=2)

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
right_frame.rowconfigure(0, weight=1)

right_paned = ttk.PanedWindow(right_frame, orient="vertical")
right_paned.grid(row=0, column=0, sticky="nsew")

queue_panel = ttk.Frame(right_paned)
queue_panel.columnconfigure(0, weight=1)
queue_panel.rowconfigure(1, weight=1)
right_paned.add(queue_panel, weight=1)

log_panel = ttk.Frame(right_paned)
log_panel.columnconfigure(0, weight=1)
log_panel.rowconfigure(2, weight=1)
right_paned.add(log_panel, weight=2)

# --- Cola ---
ttk.Label(queue_panel, text="📋  Cola de URLs pendientes:").grid(
    row=0, column=0, sticky="w", pady=(0, e(4))
)

frame_queue = ttk.Frame(queue_panel)
frame_queue.grid(row=1, column=0, sticky="nswe")
frame_queue.columnconfigure(0, weight=1)
frame_queue.rowconfigure(0, weight=1)

queue_tree = ttk.Treeview(
    frame_queue,
    columns=("url", "folder"),
    show="headings",
    selectmode="browse",
    height=12
)
queue_tree.heading("url", text="URL")
queue_tree.heading("folder", text="Carpeta destino")
queue_tree.column("url", width=e(520), minwidth=e(300), anchor="w", stretch=False)
queue_tree.column("folder", width=e(320), minwidth=e(220), anchor="w", stretch=False)
queue_tree.grid(row=0, column=0, sticky="nswe")
scroll_q = ttk.Scrollbar(frame_queue, orient="vertical", command=queue_tree.yview)
scroll_q.grid(row=0, column=1, sticky="ns")
scroll_q_horizontal = ttk.Scrollbar(
    frame_queue,
    orient="horizontal",
    command=queue_tree.xview
)
scroll_q_horizontal.grid(row=1, column=0, sticky="we")
queue_tree.configure(
    yscrollcommand=scroll_q.set,
    xscrollcommand=scroll_q_horizontal.set
)

# Menú botón derecho en la cola
def cambiar_carpeta_destino():
    sel = queue_tree.selection()
    if not sel:
        return
    item = sel[0]
    index = queue_tree.index(item)
    carpeta_actual = url_queue[index].get("folder") or os.path.expanduser("~")
    nueva_carpeta = filedialog.askdirectory(
        title="Selecciona carpeta destino para esta URL",
        initialdir=carpeta_actual or os.path.expanduser("~")
    )
    if nueva_carpeta:
        url_queue[index]["folder"] = nueva_carpeta
        queue_tree.item(item, values=(url_queue[index]["url"], nueva_carpeta))
        log(f"🗂 Carpeta actualizada: {url_queue[index]['url']}", "info")


def menu_contextual_cola(event):
    item = queue_tree.identify_row(event.y)
    if not item:
        return
    queue_tree.selection_set(item)
    menu = tk.Menu(root, tearoff=0, font=F_NORMAL)
    menu.add_command(label="✏️ Cambiar carpeta destino",
                     command=cambiar_carpeta_destino)
    menu.add_command(label="🗑 Eliminar URL seleccionada",
                     command=eliminar_url_cola)
    menu.add_command(label="🗑 Limpiar toda la cola",
                     command=limpiar_cola)
    menu.tk_popup(event.x_root, event.y_root)

queue_tree.bind("<Button-3>", menu_contextual_cola)

def eliminar_url_cola():
    sel = queue_tree.selection()
    if sel:
        item = sel[0]
        idx = queue_tree.index(item)
        queue_tree.delete(item)
        if idx < len(url_queue):
            del url_queue[idx]

def limpiar_cola():
    for item in queue_tree.get_children():
        queue_tree.delete(item)
    url_queue.clear()

# --- Log ---
ttk.Label(log_panel, text="📝  Log de operaciones:").grid(
    row=0, column=0, sticky="w", pady=(0, e(4))
)

progress_log = ttk.Progressbar(
    log_panel,
    orient="horizontal",
    mode="determinate",
    style="TProgressbar"
)
progress_log.grid(row=1, column=0, sticky="we", pady=(0, e(6)))

frame_log = ttk.Frame(log_panel)
frame_log.grid(row=2, column=0, sticky="nswe")
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

# ================== COLA Y LÓGICA DE DESCARGA ==================

url_queue = []
ultima_carpeta_destino = os.path.expanduser("~")
descarga_activa   = threading.Event()
descarga_cancelada = threading.Event()

def add_to_queue():
    global ultima_carpeta_destino
    url = entry_url.get().strip()
    if not url:
        messagebox.showwarning("Aviso", "Pega primero una URL.")
        return

    if not es_url_valida(url):
        messagebox.showwarning("Aviso", "Introduce una URL válida de YouTube.")
        return

    if any(item["url"] == url for item in url_queue):
        messagebox.showwarning("Aviso", "La URL ya está en la cola.")
        return

    carpeta_item = filedialog.askdirectory(
        title="Selecciona carpeta destino para esta URL",
        initialdir=ultima_carpeta_destino
    )
    if not carpeta_item:
            return
    ultima_carpeta_destino = carpeta_item

    url_queue.append({"url": url, "folder": carpeta_item})
    queue_tree.insert("", tk.END, values=(url, carpeta_item))
    entry_url.delete(0, tk.END)
    log(f"➕ Añadida a la cola: {url} → {carpeta_item}", "info")
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
            root.after(0, lambda: progress_log.configure(value=pct))
            set_estado(
                f"{os.path.basename(d['filename'])} — "
                f"{pct:5.1f}%  {speed/1024:5.1f} KiB/s  ETA {eta}s",
                "#0078D7"
            )
            ahora = time.monotonic()
            if (
                ahora - progreso_hook.ultimo_log >= 1
                or pct >= 100
            ):
                log(
                    f"⬇ {os.path.basename(d['filename'])} "
                    f"{pct:5.1f}%  {speed/1024:5.1f} KiB/s  ETA {eta}s",
                    "progreso"
                )
                progreso_hook.ultimo_log = ahora
    elif d.get("status") == "finished":
        nombre = os.path.basename(d["filename"])
        log(f"✅ Convertido: {nombre}", "ok")

progreso_hook.ultimo_log = 0

def construir_opts(carpeta, carpeta_ffmpeg, calidad, tipo_descarga, url, cookies_file=None):
    os.makedirs(carpeta, exist_ok=True)
    archive_file = os.path.join(carpeta, "descargados.txt")
    node_path = obtener_ruta_node()

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

    if not ffmpeg_location and getattr(sys, "_MEIPASS", None):
        ffmpeg_location = buscar_ffmpeg_en_carpetas(sys._MEIPASS)

    if not ffmpeg_location and ffmpeg_en_path():
        ffmpeg_location = None

    playlist_en_url = es_playlist_url(url)
    outtmpl = os.path.join(
        carpeta,
        "%(artist,creator,channel)s - %(track,title)s.%(ext)s"
    )
    if playlist_en_url:
        outtmpl = os.path.join(
            carpeta,
            "%(playlist_title)s",
            "%(artist,creator,channel)s - %(track,title)s.%(ext)s"
        )

    opts = {
        "outtmpl": outtmpl,
        "restrictfilenames": True,
        "continue": True,
        "embed_metadata": True,
        "embed_thumbnail": True,
        "ignoreerrors": False,
        "retries": 10,
        "fragment_retries": 10,
        "sleep_interval": 5,  # Aumentado de 1 a 5 segundos
        "max_sleep_interval": 30,  # Aumentado de 5 a 30 segundos
        "sleep_interval_requests": 1,  # Delay entre requests
        "throttled_rate": "100K",  # Limitar velocidad de descarga
        "download_archive": archive_file,
        "progress_hooks": [progreso_hook],
        "quiet": True,
        "no_warnings": False,
        "js_runtimes": {
            "node": {"path": node_path} if os.path.isfile(node_path) else {},
        },
    }
    if tipo_descarga == "MP4":
        opts.update({
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "keepvideo": False,
        })
    else:
        opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": calidad,
            }],
            "keepvideo": False,
        })

    if ffmpeg_location:
        opts["ffmpeg_location"] = ffmpeg_location
    if cookies_file:
        if cookies_file.startswith("browser:"):
            # Cookies del navegador
            navegador = cookies_file.split(":", 1)[1]
            opts["cookiesfrombrowser"] = (navegador,)
            log(f"🍪 Usando cookies del navegador: {navegador}", "info")
        elif os.path.isfile(cookies_file):
            # Archivo de cookies
            opts["cookiefile"] = cookies_file
            log(f"🍪 Usando cookies de archivo: {cookies_file}", "info")
    return opts

def normalizar_url(url):
    if "youtube.com" in url and (
        "/channel/" in url or "/user/" in url
    ):
        # Quitar /videos al final para obtener la URL base del canal
        url = url.rstrip('/').replace('/videos', '')
        canal_id = obtener_id_canal(url)
        if canal_id:
            if "/@" in url:
                nueva = f"https://www.youtube.com/@{canal_id}"
            else:
                nueva = f"https://www.youtube.com/channel/{canal_id}"
            log(f"🔎 Canal detectado → {nueva}", "warn")
            return nueva
    return url

def es_error_pagina_recarga(mensaje):
    return "The page needs to be reloaded" in mensaje

def opciones_sin_cookies(opciones):
    opciones_limpias = opciones.copy()
    opciones_limpias.pop("cookiesfrombrowser", None)
    opciones_limpias.pop("cookiefile", None)
    opciones_limpias["extractor_args"] = {
        "youtube": {"player_client": ["android"]}
    }
    return opciones_limpias

def procesar_cola(tipo_descarga):
    carpeta_ffmpeg = entry_ffmpeg.get().strip()
    cookies_file = cookies_config_var.get().strip()
    calidad       = calidad_var.get()

    total_completadas = 0

    try:
        while url_queue and not descarga_cancelada.is_set():
            entrada = url_queue.pop(0)
            children = queue_tree.get_children()
            if children:
                first_item = children[0]
                root.after(0, lambda item_id=first_item: queue_tree.delete(item_id))

            url_actual = entrada["url"]
            carpeta = entrada.get("folder")
            if not carpeta:
                log(f"❌ No hay carpeta de destino para {url_actual}. Se salta.", "error")
                continue

            ydl_opts = construir_opts(
                carpeta,
                carpeta_ffmpeg,
                calidad,
                tipo_descarga,
                url_actual,
                cookies_file
            )
            url_final = normalizar_url(url_actual)
            log(f"\n▶ Iniciando: {url_final}", "info")
            set_estado(f"Descargando: {url_final[:60]}...", "#0078D7")
            root.after(0, lambda: progress.configure(value=0))
            root.after(0, lambda: progress_log.configure(value=0))
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        ydl.download([url_final])
                    except yt_dlp.utils.DownloadError as e:
                        mensaje_error = str(e)
                        if es_error_pagina_recarga(mensaje_error) and (
                            "cookiesfrombrowser" in ydl_opts or "cookiefile" in ydl_opts
                        ):
                            log(
                                "⚠️ YouTube rechazó las cookies. Reintentando sin cookies...",
                                "warn"
                            )
                            ydl_opts_sin_cookies = opciones_sin_cookies(ydl_opts)
                            with yt_dlp.YoutubeDL(ydl_opts_sin_cookies) as ydl_sin_cookies:
                                ydl_sin_cookies.download([url_final])
                        elif "Requested format is not available" in mensaje_error:
                            log("⚠️ Formato no disponible. Reintentando con formato alternativo...", "warn")
                            ydl_opts_alt = ydl_opts.copy()
                            ydl_opts_alt["format"] = "best"
                            if tipo_descarga == "MP4":
                                ydl_opts_alt["merge_output_format"] = "mp4"
                            try:
                                with yt_dlp.YoutubeDL(ydl_opts_alt) as ydl_alt:
                                    ydl_alt.download([url_final])
                            except yt_dlp.utils.DownloadError as e2:
                                mensaje_error2 = str(e2)
                                if "Requested format is not available" in mensaje_error2:
                                    log("⚠️ Segundo intento con audio-only...", "warn")
                                    ydl_opts_alt2 = ydl_opts.copy()
                                    ydl_opts_alt2["format"] = "bestaudio/best"
                                    if tipo_descarga == "MP4":
                                        ydl_opts_alt2["merge_output_format"] = "mp4"
                                    with yt_dlp.YoutubeDL(ydl_opts_alt2) as ydl_alt2:
                                        ydl_alt2.download([url_final])
                                else:
                                    raise
                        else:
                            raise
                total_completadas += 1
                log(f"✅ URL finalizada: {url_final}", "ok")
                # Pausa adicional entre descargas para evitar rate-limiting
                if url_queue:
                    import time
                    time.sleep(10)  # 10 segundos entre URLs
            except yt_dlp.utils.DownloadError as e:
                if "cancelada" in str(e):
                    log("⏹ Cancelado por el usuario.", "warn")
                    break
                mensaje = str(e)
                registrar_error_archivo(mensaje)
                log(f"❌ Error en {url_final}: {mensaje}", "error")
            except Exception as e:
                mensaje = str(e)
                registrar_error_archivo(mensaje)
                if "Failed to decrypt with DPAPI" in mensaje:
                    log(
                        "❌ Error DPAPI: ejecuta la aplicación con el mismo usuario de Windows que usas para el navegador, "
                        "o usa un archivo de cookies manual.",
                        "error"
                    )
                else:
                    log(f"❌ Error inesperado en {url_final}: {mensaje}", "error")
    finally:
        root.after(0, lambda: btn_iniciar.config(state="normal"))
        root.after(0, lambda: btn_detener.config(state="disabled"))
        root.after(0, lambda: progress.configure(value=0))
        root.after(0, lambda: progress_log.configure(value=0))
        descarga_activa.clear()
        descarga_cancelada.clear()
        if total_completadas > 0:
            set_estado(
                f"🏁 Cola finalizada. {total_completadas} descarga(s) completada(s).",
                "#107C10"
            )
            log(
                f"\n🏁 Todo listo. {total_completadas} descarga(s) completada(s).",
                "ok"
            )
        else:
            set_estado("Cancelado.", "#D83B01")

def seleccionar_tipo_descarga():
    dialogo = tk.Toplevel(root)
    dialogo.title("Formato de descarga")
    ancho_dialogo = e(360)
    alto_dialogo = e(145)
    posicion_x = (dialogo.winfo_screenwidth() - ancho_dialogo) // 2
    posicion_y = (dialogo.winfo_screenheight() - alto_dialogo) // 2
    dialogo.geometry(
        f"{ancho_dialogo}x{alto_dialogo}+{posicion_x}+{posicion_y}"
    )
    dialogo.resizable(False, False)
    dialogo.transient(root)
    dialogo.grab_set()

    resultado = {"tipo": None}

    ttk.Label(
        dialogo,
        text="Selecciona el formato de descarga:"
    ).pack(pady=(e(18), e(12)))

    frame_botones = ttk.Frame(dialogo)
    frame_botones.pack()

    def elegir(tipo):
        resultado["tipo"] = tipo
        dialogo.destroy()

    ttk.Button(
        frame_botones,
        text="MP3",
        command=lambda: elegir("MP3"),
        width=10
    ).pack(side="left", padx=e(4))
    ttk.Button(
        frame_botones,
        text="MP4",
        command=lambda: elegir("MP4"),
        width=10
    ).pack(side="left", padx=e(4))
    ttk.Button(
        frame_botones,
        text="Cancelar",
        command=dialogo.destroy,
        width=10
    ).pack(side="left", padx=e(4))

    dialogo.protocol("WM_DELETE_WINDOW", dialogo.destroy)
    dialogo.wait_window()
    return resultado["tipo"]

def iniciar_cola():
    if not url_queue:
        messagebox.showwarning("Cola vacía", "Añade al menos una URL antes de empezar.")
        return
    if descarga_activa.is_set():
        return
    tipo_descarga = seleccionar_tipo_descarga()
    if tipo_descarga is None:
        return
    descarga_activa.set()
    descarga_cancelada.clear()
    btn_iniciar.config(state="disabled")
    btn_detener.config(state="normal")
    log("🚀 Procesando cola...", "info")
    log(f"🎵 Formato seleccionado: {tipo_descarga}", "info")
    threading.Thread(
        target=procesar_cola,
        args=(tipo_descarga,),
        daemon=True
    ).start()

def detener_todo():
    if descarga_activa.is_set():
        descarga_cancelada.set()
        log("⏹ Solicitando cancelación...", "warn")
        set_estado("Cancelando...", "#D83B01")

btn_iniciar.config(command=iniciar_cola)
btn_detener.config(command=detener_todo)

# Configurar las cookies de Firefox para evitar bloqueos 403 de YouTube.
autoconfigurar_cookies_firefox()

root.mainloop()
