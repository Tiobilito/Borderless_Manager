import win32gui
import win32con
import win32api

# Para almacenar el estado original de cada ventana
_original_states = {}

def list_windows():
    """Devuelve lista de (hwnd, título) de ventanas visibles."""
    windows = []
    def _enum(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                # Solo listamos las que NO están ya en borderless
                if hwnd not in _original_states:
                    windows.append((hwnd, title))
    win32gui.EnumWindows(_enum, None)
    return windows

def make_borderless(hwnd):
    """Aplica borderless, guarda estilo y geometría originales en _original_states."""
    # Obtener info original
    orig_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    rect = win32gui.GetWindowRect(hwnd)  # (left, top, right, bottom)
    orig_pos = {'style': orig_style, 'rect': rect}
    _original_states[hwnd] = orig_pos

    # Calcular tamaño de pantalla
    sw = win32api.GetSystemMetrics(0)
    sh = win32api.GetSystemMetrics(1)

    # Quitar bordes
    new_style = orig_style & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME)
    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)
    # Redimensionar y reposicionar
    win32gui.SetWindowPos(hwnd, None, 0, 0, sw, sh,
                          win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)

def revert_borderless(hwnd):
    """Restaura el estilo y posición original de la ventana."""
    if hwnd not in _original_states:
        return
    state = _original_states.pop(hwnd)
    orig_style = state['style']
    left, top, right, bottom = state['rect']
    width = right - left
    height = bottom - top

    # Restaurar estilo
    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, orig_style)
    # Restaurar posición y tamaño
    win32gui.SetWindowPos(hwnd, None, left, top, width, height,
                          win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)
