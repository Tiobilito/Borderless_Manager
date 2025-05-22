# utils.py
import win32gui
import win32con
import win32api
import ctypes
from ctypes import wintypes

# Guarda estado original de cada ventana:
# { hwnd: (orig_style, orig_exstyle, (left, top, right, bottom)) }
_original_states = {}

def is_borderless(hwnd):
    """¿Ya hemos aplicado borderless a esta ventana?"""
    return hwnd in _original_states

def get_original_states():
    """Devuelve una copia de los estados originales guardados."""
    return _original_states.copy()

def list_windows(exclude_hwnds=None):
    """
    Lista todas las ventanas visibles con título no vacío,
    excluyendo los hwnd en `exclude_hwnds`.
    """
    windows = []
    exclude_hwnds = set(exclude_hwnds or [])

    def _enum(hwnd, _):
        if hwnd in exclude_hwnds:
            return
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).strip()
            if title:
                windows.append((hwnd, title))

    win32gui.EnumWindows(_enum, None)
    return windows

def make_borderless(hwnd):
    """
    Aplica borderless “forzado” a la ventana hwnd:
      1. Guarda style/exstyle/rect originales.
      2. Sustituye por WS_POPUP|WS_VISIBLE.
      3. Limpia EXSTYLE que dibuja bordes.
      4. Ajusta al tamaño de pantalla.
      5. Elimina marcos DWM (Win10+).
    """
    if hwnd in _original_states:
        return  # ya aplicado

    # 1) Guardar estado original
    orig_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    orig_ex    = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    rect       = win32gui.GetWindowRect(hwnd)
    _original_states[hwnd] = (orig_style, orig_ex, rect)

    # 2) Nuevo style y exstyle limpio
    popup_style = win32con.WS_POPUP | win32con.WS_VISIBLE
    clean_ex = orig_ex & ~(win32con.WS_EX_DLGMODALFRAME |
                           win32con.WS_EX_WINDOWEDGE    |
                           win32con.WS_EX_CLIENTEDGE    |
                           win32con.WS_EX_STATICEDGE)

    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE,  popup_style)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, clean_ex)

    # 3) Maximizar al tamaño de pantalla
    sw = win32api.GetSystemMetrics(0)
    sh = win32api.GetSystemMetrics(1)
    win32gui.SetWindowPos(
        hwnd, None,
        0, 0, sw, sh,
        win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
    )

    # 4) Quitar marco DWM en Win10+ (opcional)
    try:
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        val = ctypes.c_int(0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            ctypes.c_uint(DWMWA_EXTENDED_FRAME_BOUNDS),
            ctypes.byref(val),
            ctypes.sizeof(val)
        )
    except Exception:
        pass

def revert_borderless(hwnd):
    """
    Restaura el style/exstyle/posición original de hwnd
    si antes se le aplicó make_borderless.
    """
    if hwnd not in _original_states:
        return

    orig_style, orig_ex, rect = _original_states.pop(hwnd)
    left, top, right, bottom = rect
    width, height = right - left, bottom - top

    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE,  orig_style)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, orig_ex)
    win32gui.SetWindowPos(
        hwnd, None,
        left, top, width, height,
        win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
    )

def revert_all():
    """Restaura todas las ventanas a su estado original."""
    for hwnd in list(_original_states.keys()):
        try:
            revert_borderless(hwnd)
        except Exception:
            pass
