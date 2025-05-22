import sys
import os
import threading
import json
import tkinter as tk
from tkinter import messagebox

# Mutex para evitar instancias múltiples en Windows
import win32event
import win32api
import winerror

mutex = win32event.CreateMutex(None, False, "BorderlessManagerMutex")
if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
    sys.exit(0)

from infi.systray import SysTrayIcon
import utils
import win32gui

class BorderlessApp:
    def __init__(self, root):
        self.root = root
        self.app_title = "Borderless Manager"

        # Ruta de configuración
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        self.config_path = os.path.join(base_path, "config.json")

        # Variables de configuración
        self.selected_ratio      = tk.StringVar(value="16:9")
        self.selected_resolution = tk.StringVar(value="")
        self.selected_alignment  = tk.StringVar(value="C")

        # Intentar cargar config previa
        self.load_config()

        # Título e icono de ventana
        root.title(self.app_title)
        root.geometry("800x450")
        root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self._set_icon()

        # Layout: tres columnas
        left  = tk.Frame(root)
        mid   = tk.Frame(root)
        right = tk.Frame(root)
        for frame in (left, mid, right):
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Lista de ventanas disponibles
        tk.Label(left, text="Ventanas disponibles").pack()
        self.lst_avail = tk.Listbox(left, width=50, height=20)
        self.lst_avail.pack(fill=tk.BOTH, expand=True)

        # Lista de ventanas borderless activas
        tk.Label(right, text="Borderless activas").pack()
        self.lst_active = tk.Listbox(right, width=50, height=20)
        self.lst_active.pack(fill=tk.BOTH, expand=True)

        # Botones de acción
        tk.Button(mid, text="→ Aplicar",   command=self.apply_selected).pack(pady=10)
        tk.Button(mid, text="← Revertir",  command=self.revert_selected).pack(pady=10)
        tk.Button(mid, text="🔄 Refrescar", command=self.refresh_lists).pack(pady=10)
        tk.Button(mid, text="⚙️ Configurar", command=self.open_config_window).pack(pady=10)

        # Carga inicial de listas y setup del tray
        self.refresh_lists()
        self._setup_tray()

    def _set_icon(self):
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        icon_path = os.path.join(base_path, "resources", "icon.ico")
        try:
            self.root.iconbitmap(icon_path)
        except Exception:
            pass

    def load_config(self):
        """Carga la configuración desde disk si existe."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.selected_ratio.set(cfg.get("ratio", self.selected_ratio.get()))
            self.selected_resolution.set(cfg.get("resolution", self.selected_resolution.get()))
            self.selected_alignment.set(cfg.get("alignment", self.selected_alignment.get()))
        except (FileNotFoundError, json.JSONDecodeError):
            # No existe o corrupto: usar valores por defecto
            pass

    def save_config(self):
        """Guarda la configuración actual a disk."""
        cfg = {
            "ratio":      self.selected_ratio.get(),
            "resolution": self.selected_resolution.get(),
            "alignment":  self.selected_alignment.get()
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error al guardar configuración", str(e))

    def refresh_lists(self):
        self._load_available_windows()
        self._load_active_windows()

    def _load_available_windows(self):
        self.lst_avail.delete(0, tk.END)
        exclude = [self.root.winfo_id()]
        all_windows = utils.list_windows(exclude_hwnds=exclude)
        self.avail = [
            (hwnd, title)
            for hwnd, title in all_windows
            if not utils.is_borderless(hwnd) and title != self.app_title
        ]
        for hwnd, title in self.avail:
            self.lst_avail.insert(tk.END, f"{hwnd} - {title}")

    def _load_active_windows(self):
        self.lst_active.delete(0, tk.END)
        orig_states = utils.get_original_states()
        self.active = [(hwnd, win32gui.GetWindowText(hwnd)) for hwnd in orig_states]
        for hwnd, title in self.active:
            self.lst_active.insert(tk.END, f"{hwnd} - {title}")

    def apply_selected(self):
        sel = self.lst_avail.curselection()
        if not sel:
            messagebox.showwarning("Error", "Selecciona una ventana para aplicar.")
            return
        hwnd, _ = self.avail[sel[0]]
        try:
            if self.selected_resolution.get():
                w, h = map(int, self.selected_resolution.get().split("x"))
                align = self.selected_alignment.get()
                utils.make_borderless(hwnd, w, h, alignment=align)
            else:
                utils.make_borderless(hwnd, alignment=self.selected_alignment.get())
            self.refresh_lists()
        except Exception as e:
            messagebox.showerror("Error al aplicar borderless", str(e))

    def revert_selected(self):
        sel = self.lst_active.curselection()
        if not sel:
            messagebox.showwarning("Error", "Selecciona una ventana para revertir.")
            return
        hwnd, _ = self.active[sel[0]]
        try:
            utils.revert_borderless(hwnd)
            self.refresh_lists()
        except Exception as e:
            messagebox.showerror("Error al revertir borderless", str(e))

    def hide_window(self):
        self.root.withdraw()

    def show_window(self, systray=None):
        self.root.after(0, self.root.deiconify)

    def quit_app(self, systray=None):
        utils.revert_all()
        self.root.after(0, self.root.destroy)

    def _setup_tray(self):
        menu_options = (("Abrir Manager", None, self.show_window),)
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        icon_path = os.path.join(base_path, "resources", "icon.ico")
        self.tray = SysTrayIcon(icon_path, self.app_title, menu_options,
                               on_quit=self.quit_app, default_menu_index=0)
        threading.Thread(target=self.tray.start, daemon=True).start()

    def open_config_window(self):
        config = tk.Toplevel(self.root)
        config.update_idletasks()
        win_w, win_h = 350, 400
        # posición y tamaño de la ventana principal
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        # cálculo de coords para centrar
        x = root_x + (root_w  - win_w) // 2
        y = root_y + (root_h - win_h) // 2
        config.geometry(f"{win_w}x{win_h}+{x}+{y}")
        config.title("Configuración Borderless")
        config.geometry("350x400")
        config.transient(self.root)
        config.grab_set()

        aspect_ratios = {
            "16:9": [(1920,1080),(1600,900),(1280,720)],
            "4:3":  [(1024,768),(800,600)],
            "21:9": [(2560,1080),(3440,1440)],
        }

        # Aspect Ratio
        tk.Label(config, text="Aspect Ratio").pack(pady=5)
        ratio_menu = tk.OptionMenu(
            config,
            self.selected_ratio,
            *aspect_ratios.keys(),
            command=lambda _: update_resolutions()
        )
        ratio_menu.pack()

        # Resolución
        tk.Label(config, text="Resolución").pack(pady=5)
        self.res_menu = tk.OptionMenu(config, self.selected_resolution, "")
        self.res_menu.pack()

        def update_resolutions():
            menu = self.res_menu["menu"]
            menu.delete(0, "end")
            for w,h in aspect_ratios[self.selected_ratio.get()]:
                s = f"{w}x{h}"
                menu.add_command(label=s, command=lambda v=s: self.selected_resolution.set(v))
            w0,h0 = aspect_ratios[self.selected_ratio.get()][0]
            self.selected_resolution.set(f"{w0}x{h0}")

        update_resolutions()

        # Posición (“cruceta”)
        tk.Label(config, text="Posición en pantalla").pack(pady=5)
        grid = tk.Frame(config)
        grid.pack()
        coords = [
            [("NW",0,0),("N",1,0),("NE",2,0)],
            [("W",0,1),("C",1,1),("E",2,1)],
            [("SW",0,2),("S",1,2),("SE",2,2)],
        ]
        for label,x,y in [cell for row in coords for cell in row]:
            rb = tk.Radiobutton(
                grid,
                variable=self.selected_alignment,
                value=label,
                text=label
            )
            rb.grid(column=x, row=y, padx=5, pady=5)

        # Detectar resolución y aspect ratio automático
        def detect_resolution():
            sw = win32api.GetSystemMetrics(0)
            sh = win32api.GetSystemMetrics(1)
            # elegir aspect ratio más cercano
            target = sw / sh
            ratios = {k: eval(k.replace(":", "/")) for k in aspect_ratios.keys()}
            best = min(ratios, key=lambda k: abs(ratios[k] - target))
            self.selected_ratio.set(best)
            update_resolutions()
            self.selected_resolution.set(f"{sw}x{sh}")

        tk.Button(config, text="📏 Detectar resolución actual", command=detect_resolution).pack(pady=10)

        # Confirmar / Cancelar
        def confirm():
            self.save_config()
            config.destroy()

        tk.Button(config, text="✅ Confirmar", command=confirm).pack(pady=5)

        def cancel():
            # recargar última config guardada
            self.load_config()
            config.destroy()

        tk.Button(config, text="❌ Cancelar", command=cancel).pack(pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app  = BorderlessApp(root)
    root.mainloop()
