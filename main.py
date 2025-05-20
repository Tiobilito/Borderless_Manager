import threading
import tkinter as tk
from tkinter import messagebox
from infi.systray import SysTrayIcon
from PIL import Image  # si necesitas manipular el icono, aunque infi.systray carga directamente el .ico

import utils
import win32gui

class BorderlessApp:
    def __init__(self, root):
        self.root = root
        root.title("Borderless Manager")
        root.geometry("800x450")
        # Al cerrar la ventana principal, solo la ocultamos
        root.protocol("WM_DELETE_WINDOW", self.hide_window)

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

        # Carga inicial de listas y setup del tray
        self.refresh_lists()
        self._setup_tray()

    def refresh_lists(self):
        """Recarga las dos listas desde utils."""
        self.lst_avail.delete(0, tk.END)
        self.lst_active.delete(0, tk.END)

        # Ventanas no borderless aún
        self.avail = utils.list_windows()
        for hwnd, title in self.avail:
            self.lst_avail.insert(tk.END, f"{hwnd} - {title}")

        # Ventanas que ya tienen borderless
        self.active = [(h, win32gui.GetWindowText(h)) for h in utils._original_states]
        for hwnd, title in self.active:
            self.lst_active.insert(tk.END, f"{hwnd} - {title}")

    def apply_selected(self):
        sel = self.lst_avail.curselection()
        if not sel:
            messagebox.showwarning("Error", "Selecciona una ventana para aplicar.")
            return
        hwnd, _ = self.avail[sel[0]]
        try:
            utils.make_borderless(hwnd)
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
            messagebox.showerror("Error al revertir", str(e))

    def hide_window(self):
        """Oculta la ventana principal en lugar de cerrar la app."""
        self.root.withdraw()

    def show_window(self, systray=None):
        """Muestra la ventana principal (clic izquierdo en el icono)."""
        self.root.after(0, self.root.deiconify)

    def quit_app(self, systray=None):
        """Restaura todas las ventanas y cierra la aplicación."""
        utils.revert_all()
        self.root.after(0, self.root.destroy)

    def _setup_tray(self):
        """Configura el icono en la bandeja y su menú."""
        # Usamos una tupla de opciones para que infi.systray pueda concatenar correctamente
        menu_options = (
            ("Abrir Manager", None, self.show_window),
        )
        self.tray = SysTrayIcon(
            "resources/icon.ico",         # Ruta al icono .ico
            "Borderless Manager",         # Tooltip
            menu_options,
            on_quit=self.quit_app,        # Se ejecuta al seleccionar "Quit"
            default_menu_index=0          # Clic izquierdo ejecuta menu_options[0]
        )
        # Ejecutar el tray icon en un hilo demonio para no bloquear la UI
        threading.Thread(target=self.tray.start, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = BorderlessApp(root)
    root.mainloop()
