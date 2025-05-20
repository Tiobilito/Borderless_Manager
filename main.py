import tkinter as tk
from tkinter import messagebox
from utils import list_windows, make_borderless, revert_borderless, _original_states

class BorderlessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Borderless Manager")
        self.root.geometry("800x450")

        # Frames para organizar
        left_frame = tk.Frame(root)
        middle_frame = tk.Frame(root)
        right_frame = tk.Frame(root)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        middle_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Listbox de ventanas disponibles
        tk.Label(left_frame, text="Ventanas disponibles").pack()
        self.lst_avail = tk.Listbox(left_frame, width=50, height=20)
        self.lst_avail.pack(fill=tk.BOTH, expand=True)

        # Listbox de ventanas borderless activas
        tk.Label(right_frame, text="Borderless activas").pack()
        self.lst_active = tk.Listbox(right_frame, width=50, height=20)
        self.lst_active.pack(fill=tk.BOTH, expand=True)

        # Botones
        btn_apply = tk.Button(middle_frame, text="→ Aplicar", command=self.apply_selected)
        btn_revert = tk.Button(middle_frame, text="← Revertir", command=self.revert_selected)
        btn_refresh = tk.Button(middle_frame, text="🔄 Refrescar", command=self.refresh_lists)
        btn_apply.pack(pady=10)
        btn_revert.pack(pady=10)
        btn_refresh.pack(pady=10)

        self.refresh_lists()

    def refresh_lists(self):
        # Recarga ambas listas
        self.lst_avail.delete(0, tk.END)
        self.lst_active.delete(0, tk.END)

        self.avail = list_windows()
        for hwnd, title in self.avail:
            self.lst_avail.insert(tk.END, f"{hwnd} - {title}")

        # Las activas las obtenemos de _original_states
        self.active = [(hwnd, win32gui.GetWindowText(hwnd)) for hwnd in _original_states]
        for hwnd, title in self.active:
            self.lst_active.insert(tk.END, f"{hwnd} - {title}")

    def apply_selected(self):
        sel = self.lst_avail.curselection()
        if not sel:
            messagebox.showwarning("Error", "Selecciona una ventana para aplicar.")
            return
        index = sel[0]
        hwnd, _ = self.avail[index]
        try:
            make_borderless(hwnd)
            self.refresh_lists()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def revert_selected(self):
        sel = self.lst_active.curselection()
        if not sel:
            messagebox.showwarning("Error", "Selecciona una ventana para revertir.")
            return
        index = sel[0]
        hwnd, _ = self.active[index]
        try:
            revert_borderless(hwnd)
            self.refresh_lists()
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    # Necesitamos win32gui aquí para refrescar títulos de activas
    import win32gui
    root = tk.Tk()
    app = BorderlessApp(root)
    root.mainloop()
