import win32gui
import win32con
import win32api
import ctypes
from ctypes import wintypes

# Guarda estado original de cada ventana:
# { hwnd: (orig_style, orig_exstyle, (left, top, right, bottom)) }
_original_states = {}

def is_borderless(hwnd):
    return hwnd in _original_states

def get_original_states():
    return _original_states.copy()

def list_windows(exclude_hwnds=None):
    windows = []
    exclude = set(exclude_hwnds or [])
    def _enum(h, _):
        if h in exclude:
            return
        if win32gui.IsWindowVisible(h):
            t = win32gui.GetWindowText(h).strip()
            if t:
                windows.append((h, t))
    win32gui.EnumWindows(_enum, None)
    return windows

def make_borderless(hwnd, custom_width=None, custom_height=None, alignment="C"):
    if hwnd in _original_states:
        return

    # Guardar estado original
    orig_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    orig_ex    = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    rect       = win32gui.GetWindowRect(hwnd)
    _original_states[hwnd] = (orig_style, orig_ex, rect)

    # Aplicar estilos borderless
    popup = win32con.WS_POPUP | win32con.WS_VISIBLE
    clean_ex = orig_ex & ~(win32con.WS_EX_DLGMODALFRAME |
                           win32con.WS_EX_WINDOWEDGE    |
                           win32con.WS_EX_CLIENTEDGE    |
                           win32con.WS_EX_STATICEDGE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, popup)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, clean_ex)

    # Determinar tamaño
    screen_w = win32api.GetSystemMetrics(0)
    screen_h = win32api.GetSystemMetrics(1)
    w = custom_width  or screen_w
    h = custom_height or screen_h

    # Calcular posición según alignment
    offs = {
        "NW": (0, 0),
        "N":  ((screen_w - w)//2, 0),
        "NE": (screen_w - w, 0),
        "W":  (0, (screen_h - h)//2),
        "C":  ((screen_w - w)//2, (screen_h - h)//2),
        "E":  (screen_w - w, (screen_h - h)//2),
        "SW": (0, screen_h - h),
        "S":  ((screen_w - w)//2, screen_h - h),
        "SE": (screen_w - w, screen_h - h),
    }
    x, y = offs.get(alignment, (0, 0))

    win32gui.SetWindowPos(
        hwnd, None,
        x, y, w, h,
        win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
    )

    # Quitar marco DWM en Win10+
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
    if hwnd not in _original_states:
        return

    orig_style, orig_ex, rect = _original_states.pop(hwnd)
    left, top, right, bottom = rect
    width, height = right - left, bottom - top

    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, orig_style)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, orig_ex)
    win32gui.SetWindowPos(
        hwnd, None,
        left, top, width, height,
        win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
    )

def revert_all():
    for hwnd in list(_original_states.keys()):
        try:
            revert_borderless(hwnd)
        except Exception:
            pass
