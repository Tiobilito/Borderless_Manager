import threading
import tkinter as tk
from tkinter import messagebox
from PIL import Image
from pystray import Icon, MenuItem, Menu

import utils
import win32gui

class BorderlessApp:
    def __init__(self, root):
        self.root = root
        root.title("Borderless Manager")
        root.geometry("800x450")

        # Evita que cierre, solo oculta
        root.protocol("WM_DELETE_WINDOW", self.hide_window)

        # Layout
        left = tk.Frame(root); mid = tk.Frame(root); right = tk.Frame(root)
        for f in (left, mid, right): f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(left, text="Ventanas disponibles").pack()
        self.lst_avail = tk.Listbox(left, width=50, height=20); self.lst_avail.pack(fill=tk.BOTH, expand=True)

        tk.Label(right, text="Borderless activas").pack()
        self.lst_active = tk.Listbox(right, width=50, height=20); self.lst_active.pack(fill=tk.BOTH, expand=True)

        tk.Button(mid, text="→ Aplicar",   command=self.apply_selected).pack(pady=10)
        tk.Button(mid, text="← Revertir",  command=self.revert_selected).pack(pady=10)
        tk.Button(mid, text="🔄 Refrescar", command=self.refresh_lists).pack(pady=10)

        self.refresh_lists()
        self._setup_tray()

    def refresh_lists(self):
        self.lst_avail.delete(0, tk.END)
        self.lst_active.delete(0, tk.END)

        self.avail = utils.list_windows()
        for hwnd, title in self.avail:
            self.lst_avail.insert(tk.END, f"{hwnd} - {title}")

        self.active = [(h, win32gui.GetWindowText(h)) for h in utils._original_states]
        for hwnd, title in self.active:
            self.lst_active.insert(tk.END, f"{hwnd} - {title}")

    def apply_selected(self):
        sel = self.lst_avail.curselection()
        if not sel:
            messagebox.showwarning("Error", "Selecciona una ventana.")
            return
        hwnd, _ = self.avail[sel[0]]
        try:
            utils.make_borderless(hwnd)
            self.refresh_lists()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def revert_selected(self):
        sel = self.lst_active.curselection()
        if not sel:
            messagebox.showwarning("Error", "Selecciona una ventana.")
            return
        hwnd, _ = self.active[sel[0]]
        try:
            utils.revert_borderless(hwnd)
            self.refresh_lists()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def hide_window(self):
        self.root.withdraw()

    def show_window(self, icon, item):
        self.root.after(0, self.root.deiconify)

    def quit_app(self, icon, item):
        # Revertir todo antes de salir
        utils.revert_all()
        icon.stop()
        self.root.after(0, self.root.destroy)

    def _setup_tray(self):
        # Carga icono
        image = Image.open("resources/icon.png")
        menu = Menu(
            MenuItem("Abrir Manager", self.show_window),
            MenuItem("Salir",         self.quit_app)
        )
        self.tray_icon = Icon("BorderlessManager", image, "Borderless", menu)
        # Ejecutar icon.run() en hilo aparte
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = BorderlessApp(root)
    root.mainloop()
