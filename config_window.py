import tkinter as tk
import win32api
import json
from constants import BASE_PATH, CONFIG_PATH

class ConfigWindow:
    def __init__(self, parent, selected_ratio, selected_resolution, selected_alignment):
        self.config = tk.Toplevel(parent)
        self.config.update_idletasks()
        
        # Variables de configuración pasadas desde el padre
        self.selected_ratio = selected_ratio
        self.selected_resolution = selected_resolution
        self.selected_alignment = selected_alignment

        # Configuración de la ventana
        win_w, win_h = 350, 400
        root_x = parent.winfo_rootx()
        root_y = parent.winfo_rooty()
        root_w = parent.winfo_width()
        root_h = parent.winfo_height()
        x = root_x + (root_w - win_w) // 2
        y = root_y + (root_h - win_h) // 2
        
        self.config.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.config.title("Configuración Borderless")
        self.config.transient(parent)
        self.config.grab_set()

        self._setup_ui()

    def _setup_ui(self):
        self.aspect_ratios = {
            "16:9": [(1920,1080),(1600,900),(1280,720)],
            "4:3":  [(1024,768),(800,600)],
            "21:9": [(2560,1080),(3440,1440)],
        }

        # Aspect Ratio
        tk.Label(self.config, text="Aspect Ratio").pack(pady=5)
        ratio_menu = tk.OptionMenu(
            self.config,
            self.selected_ratio,
            *self.aspect_ratios.keys(),
            command=lambda _: self.update_resolutions()
        )
        ratio_menu.pack()

        # Resolución
        tk.Label(self.config, text="Resolución").pack(pady=5)
        self.res_menu = tk.OptionMenu(self.config, self.selected_resolution, "")
        self.res_menu.pack()

        # Posición
        tk.Label(self.config, text="Posición en pantalla").pack(pady=5)
        self._setup_position_grid()

        # Botones
        tk.Button(self.config, text="📏 Detectar resolución actual", 
                 command=self.detect_resolution).pack(pady=10)
        tk.Button(self.config, text="✅ Confirmar", 
                 command=self.confirm).pack(pady=5)
        tk.Button(self.config, text="❌ Cancelar", 
                 command=self.cancel).pack(pady=5)

        self.update_resolutions()

    def _setup_position_grid(self):
        grid = tk.Frame(self.config)
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

    def update_resolutions(self):
        menu = self.res_menu["menu"]
        menu.delete(0, "end")
        for w,h in self.aspect_ratios[self.selected_ratio.get()]:
            s = f"{w}x{h}"
            menu.add_command(label=s, command=lambda v=s: self.selected_resolution.set(v))
        w0,h0 = self.aspect_ratios[self.selected_ratio.get()][0]
        self.selected_resolution.set(f"{w0}x{h0}")

    def detect_resolution(self):
        sw = win32api.GetSystemMetrics(0)
        sh = win32api.GetSystemMetrics(1)
        target = sw / sh
        ratios = {k: eval(k.replace(":", "/")) for k in self.aspect_ratios.keys()}
        best = min(ratios, key=lambda k: abs(ratios[k] - target))
        self.selected_ratio.set(best)
        self.update_resolutions()
        self.selected_resolution.set(f"{sw}x{sh}")

    def confirm(self):
        self.save_config()
        self.config.destroy()

    def cancel(self):
        self.load_config()
        self.config.destroy()

    def save_config(self):
        cfg = {
            "ratio": self.selected_ratio.get(),
            "resolution": self.selected_resolution.get(),
            "alignment": self.selected_alignment.get()
        }
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            tk.messagebox.showerror("Error al guardar configuración", str(e))

    def load_config(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.selected_ratio.set(cfg.get("ratio", self.selected_ratio.get()))
            self.selected_resolution.set(cfg.get("resolution", self.selected_resolution.get()))
            self.selected_alignment.set(cfg.get("alignment", self.selected_alignment.get()))
        except (FileNotFoundError, json.JSONDecodeError):
            pass
