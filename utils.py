import win32gui
import win32con
import win32api

# Estado original de cada ventana: { hwnd: {'style':…, 'rect':(l,t,r,b)} }
_original_states = {}

def list_windows():
    windows = []
    def _enum(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and hwnd not in _original_states:
                windows.append((hwnd, title))
    win32gui.EnumWindows(_enum, None)
    return windows

def make_borderless(hwnd):
    # Guardar estado original
    orig_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    rect = win32gui.GetWindowRect(hwnd)
    _original_states[hwnd] = {'style': orig_style, 'rect': rect}

    # Quitar bordes y maximizar
    sw, sh = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)
    new_style = orig_style & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME)
    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)
    win32gui.SetWindowPos(hwnd, None, 0, 0, sw, sh,
                          win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)

def revert_borderless(hwnd):
    if hwnd not in _original_states:
        return
    state = _original_states.pop(hwnd)
    left, top, right, bottom = state['rect']
    width, height = right - left, bottom - top

    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, state['style'])
    win32gui.SetWindowPos(hwnd, None, left, top, width, height,
                          win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)

def revert_all():
    """Restaura todas las ventanas a su estilo y posición original."""
    for hwnd in list(_original_states.keys()):
        try:
            revert_borderless(hwnd)
        except Exception:
            pass
