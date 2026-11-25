import os
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path

import uvicorn
import webview

from backend import ICON_ICO, init_db
from backend.api import app


def _find_free_port(preferred: int = 8765) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", preferred)) != 0:
            return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(url: str, timeout: float = 8.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.1)
    return False


def _set_windows_icon(title: str = "Nexo"):
    """Define o ícone oficial nexo_icon.ico na janela nativa do Windows e na Barra de Tarefas."""
    if sys.platform != "win32" or not ICON_ICO.exists():
        return
    try:
        import ctypes

        user32 = ctypes.windll.user32
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        LR_DEFAULTSIZE = 0x00000040
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        GCLP_HICON = -14
        GCLP_HICONSM = -34

        hicon_small = user32.LoadImageW(None, str(ICON_ICO), IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
        hicon_big = user32.LoadImageW(None, str(ICON_ICO), IMAGE_ICON, 48, 48, LR_LOADFROMFILE)
        if not hicon_big:
            hicon_big = user32.LoadImageW(None, str(ICON_ICO), IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)
        if not hicon_small:
            hicon_small = hicon_big
        if not hicon_small and not hicon_big:
            return

        set_class_long = getattr(user32, "SetClassLongPtrW", user32.SetClassLongW)
        set_class_long.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]

        for _ in range(40):
            hwnd = user32.FindWindowW(None, title)
            if hwnd:
                if hicon_small:
                    user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
                    set_class_long(hwnd, GCLP_HICONSM, hicon_small)
                if hicon_big:
                    user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
                    set_class_long(hwnd, GCLP_HICON, hicon_big)
                break
            time.sleep(0.1)
    except Exception:
        pass


def _focus_existing_window(title: str = "Nexo") -> None:
    """Restaura e traz para frente a janela do Nexo já em execução."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, title)
        if hwnd:
            SW_SHOW = 5
            SW_RESTORE = 9
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, SW_RESTORE)
            else:
                user32.ShowWindow(hwnd, SW_SHOW)
            user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def _acquire_single_instance_mutex(name: str = "Local\\LeonanGarcia.Nexo.v2.SingleInstance"):
    """Garante instância única no Windows via Mutex nomeado.

    Retorna o handle do mutex se esta for a primeira instância, ou None se já existir outra.
    """
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        ERROR_ALREADY_EXISTS = 183
        handle = kernel32.CreateMutexW(None, False, name)
        if not handle:
            return True
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return None
        return (kernel32, handle)
    except Exception:
        return True


def main():
    _instance_mutex = _acquire_single_instance_mutex()
    if _instance_mutex is None:
        _focus_existing_window("Nexo")
        return

    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("LeonanGarcia.Nexo.v2")
        except Exception:
            pass

    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

    init_db()
    port = _find_free_port(8765)
    base_url = f"http://127.0.0.1:{port}"

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        log_config=None,
        access_log=False,
    )
    server = uvicorn.Server(config)

    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    _wait_for_server(f"{base_url}/api/status")

    # Calcula dimensões ideais centralizadas na área de trabalho útil do Windows (sem cobrir a barra Iniciar)
    w, h = 1280, 800
    x, y = None, None
    min_w, min_h = 920, 560
    try:
        import ctypes
        from ctypes import wintypes

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", wintypes.LONG),
                ("top", wintypes.LONG),
                ("right", wintypes.LONG),
                ("bottom", wintypes.LONG),
            ]

        rect = RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            sw = max(640, rect.right - rect.left)
            sh = max(480, rect.bottom - rect.top)
            w = min(1280, int(sw * 0.94))
            h = min(800, int(sh * 0.88))
            x = rect.left + max(0, (sw - w) // 2)
            y = rect.top + max(0, (sh - h) // 2)
            min_w = min(920, max(640, sw - 40))
            min_h = min(560, max(480, sh - 40))
    except Exception:
        pass

    window_kwargs = {
        "width": w,
        "height": h,
        "min_size": (min_w, min_h),
        "maximized": True,
        "background_color": "#F4F7FC",
        "text_select": False,
    }
    if x is not None and y is not None:
        window_kwargs["x"] = x
        window_kwargs["y"] = y

    window = webview.create_window(
        "Nexo",
        base_url,
        **window_kwargs,
    )

    def on_shown():
        threading.Thread(target=_set_windows_icon, args=("Nexo",), daemon=True).start()

    window.events.shown += on_shown
    webview.start(gui="edgechromium")
    server.should_exit = True
    if isinstance(_instance_mutex, tuple):
        try:
            kernel32, handle = _instance_mutex
            kernel32.CloseHandle(handle)
        except Exception:
            pass


if __name__ == "__main__":
    main()
