import os
import sys
import json
import tkinter as tk
from tkinter import messagebox, simpledialog
import utils
from constants import BORDERLESS_PROGRAMS_PATH

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

def open_borderless_programs_window(parent):
    win = tk.Toplevel(parent)
    win.title("Borderless automático")
    win.geometry("400x400")
    win.transient(parent)
    win.grab_set()

    tk.Label(win, text="Títulos de ventanas a aplicar borderless automáticamente:").pack(pady=5)
    lst = tk.Listbox(win, width=50, height=15)
    lst.pack(fill=tk.BOTH, expand=True, padx=10)

    def refresh():
        lst.delete(0, tk.END)
        for title in sorted(load_borderless_programs()):
            lst.insert(tk.END, title)
    refresh()

    def add_title():
        # Ventana para seleccionar entre ventanas abiertas
        sel_win = tk.Toplevel(win)
        sel_win.title("Seleccionar ventana abierta")
        sel_win.geometry("350x350")
        sel_win.transient(win)
        sel_win.grab_set()

        tk.Label(sel_win, text="Selecciona un título de ventana:").pack(pady=5)
        avail_lst = tk.Listbox(sel_win, width=45, height=12)
        avail_lst.pack(fill=tk.BOTH, expand=True, padx=10)

        def load_avail():
            avail_lst.delete(0, tk.END)
            # Excluir títulos ya en la lista de borderless
            current = load_borderless_programs()
            # Obtener títulos únicos de ventanas abiertas
            titles = []
            for hwnd, title in utils.list_windows():
                if title and title not in current and title not in titles:
                    avail_lst.insert(tk.END, title)
                    titles.append(title)

        load_avail()

        def on_select():
            sel = avail_lst.curselection()
            if not sel:
                return
            title = avail_lst.get(sel[0])
            progs = load_borderless_programs()
            progs.add(title)
            save_borderless_programs(progs)
            refresh()
            sel_win.destroy()

        btn_frame = tk.Frame(sel_win)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="🔄 Refrescar", command=load_avail).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Agregar", command=on_select).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancelar", command=sel_win.destroy).pack(side=tk.LEFT, padx=5)

    def remove_selected():
        sel = lst.curselection()
        if not sel:
            return
        title = lst.get(sel[0])
        progs = load_borderless_programs()
        if title in progs:
            progs.remove(title)
            save_borderless_programs(progs)
            refresh()

    btns = tk.Frame(win)
    btns.pack(pady=10)
    tk.Button(btns, text="➕ Agregar", command=add_title).pack(side=tk.LEFT, padx=5)
    tk.Button(btns, text="➖ Quitar", command=remove_selected).pack(side=tk.LEFT, padx=5)
    tk.Button(btns, text="Cerrar", command=win.destroy).pack(side=tk.LEFT, padx=5)
