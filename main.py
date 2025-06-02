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
from borderless_programs_window import open_borderless_programs_window, BORDERLESS_PROGRAMS_PATH

def load_borderless_programs():
    try:
        with open(BORDERLESS_PROGRAMS_PATH, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_borderless_programs(programs):
    try:
        with open(BORDERLESS_PROGRAMS_PATH, "w", encoding="utf-8") as f:
            json.dump(sorted(list(programs)), f, indent=2, ensure_ascii=False)
    except Exception as e:
        messagebox.showerror("Error al guardar programas borderless", str(e))

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
        tk.Button(mid, text="📝 Borderless auto...", command=self.open_borderless_programs).pack(pady=10)

        # Carga inicial de listas y setup del tray
        self._manual_refresh = False

        # Lista en memoria de títulos con borderless activo
        self.active_borderless_titles = set()

        self.refresh_lists()
        self._setup_tray()

        # Hilo de comprobación periódica
        self._stop_check = threading.Event()
        threading.Thread(target=self._periodic_check, daemon=True).start()

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
        self._manual_refresh = True
        self._load_available_windows()
        self._load_active_windows()
        self._manual_refresh = False

    def _periodic_check(self):
        import time
        from borderless_programs_window import load_borderless_programs
        while not getattr(self, "_stop_check", None) or not self._stop_check.is_set():
            self._sync_borderless_state()
            time.sleep(2)

    def _sync_borderless_state(self):
        from borderless_programs_window import load_borderless_programs
        borderless_programs = load_borderless_programs()
        all_windows = utils.list_windows()
        open_titles = set(title for hwnd, title in all_windows)
        # 1. Aplica borderless a los programas del JSON que estén abiertos y no estén activos
        for title in borderless_programs:
            if title in open_titles and title not in self.active_borderless_titles:
                for hwnd, t in all_windows:
                    if t == title and not utils.is_borderless(hwnd):
                        try:
                            utils.make_borderless(hwnd, alignment=self.selected_alignment.get())
                            self.active_borderless_titles.add(title)
                        except Exception:
                            pass
        # 2. Elimina de la lista en memoria los que ya no están abiertos
        to_remove = set()
        for title in self.active_borderless_titles:
            if title not in open_titles:
                to_remove.add(title)
        if to_remove:
            self.active_borderless_titles -= to_remove
        # 3. Actualiza la lista de borderless activas en la GUI
        self.root.after(0, self._load_active_windows)

    def _load_available_windows(self):
        if not self._manual_refresh and hasattr(self, "avail"):
            return  # No refrescar automáticamente
        self.lst_avail.delete(0, tk.END)
        exclude = [self.root.winfo_id()]
        all_windows = utils.list_windows(exclude_hwnds=exclude)
        self.avail = [
            (hwnd, title)
            for hwnd, title in all_windows
            if not utils.is_borderless(hwnd) and title != self.app_title
        ]
        # Mostrar solo nombres (sin IDs)
        titles = []
        for hwnd, title in self.avail:
            if title not in titles:
                self.lst_avail.insert(tk.END, title)
                titles.append(title)

    def _load_active_windows(self):
        # Guardar selección actual antes de refrescar
        sel = self.lst_active.curselection()
        selected_title = self.lst_active.get(sel[0]) if sel else None

        self.lst_active.delete(0, tk.END)
        orig_states = utils.get_original_states()
        # Agrupar por título (puede haber varias ventanas con el mismo título)
        titles = set()
        self.active = []
        for hwnd in orig_states:
            title = win32gui.GetWindowText(hwnd)
            if title and title not in titles:
                self.active.append((hwnd, title))
                self.lst_active.insert(tk.END, title)
                titles.add(title)
        # Actualiza la lista en memoria de títulos activos
        self.active_borderless_titles = titles

        # Restaurar selección si sigue existiendo
        if selected_title:
            for idx, (hwnd, title) in enumerate(self.active):
                if title == selected_title:
                    self.lst_active.selection_set(idx)
                    break

    def apply_selected(self):
        sel = self.lst_avail.curselection()
        if not sel:
            messagebox.showwarning("Error", "Selecciona una ventana para aplicar.")
            return
        selected_title = self.lst_avail.get(sel[0])
        all_windows = utils.list_windows()
        applied = False
        for hwnd, title in all_windows:
            if title == selected_title and not utils.is_borderless(hwnd):
                try:
                    if self.selected_resolution.get():
                        w, h = map(int, self.selected_resolution.get().split("x"))
                        align = self.selected_alignment.get()
                        utils.make_borderless(hwnd, w, h, alignment=align)
                    else:
                        utils.make_borderless(hwnd, alignment=self.selected_alignment.get())
                    applied = True
                    self.active_borderless_titles.add(selected_title)
                except Exception as e:
                    messagebox.showerror("Error al aplicar borderless", str(e))
        self._load_active_windows()

    def revert_selected(self):
        sel = self.lst_active.curselection()
        if not sel:
            messagebox.showwarning("Error", "Selecciona una ventana para revertir.")
            return
        # Usar self.active para obtener el hwnd correcto
        selected_idx = sel[0]
        if not hasattr(self, "active") or selected_idx >= len(self.active):
            messagebox.showwarning("Error", "Selección inválida.")
            return
        hwnd, selected_title = self.active[selected_idx]
        orig_states = utils.get_original_states()
        reverted = False
        # Buscar por hwnd directamente
        if hwnd in orig_states:
            try:
                utils.revert_borderless(hwnd)
                reverted = True
            except Exception as e:
                messagebox.showerror("Error al revertir borderless", str(e))
        if reverted and selected_title in self.active_borderless_titles:
            self.active_borderless_titles.remove(selected_title)
        self._load_active_windows()

    def hide_window(self):
        self.root.withdraw()

    def show_window(self, systray=None):
        self.root.after(0, self.root.deiconify)

    def quit_app(self, systray=None):
        utils.revert_all()
        if hasattr(self, "_stop_check"):
            self._stop_check.set()
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

    def open_borderless_programs(self):
        open_borderless_programs_window(self.root)


if __name__ == "__main__":
    root = tk.Tk()
    app  = BorderlessApp(root)
    root.mainloop()
