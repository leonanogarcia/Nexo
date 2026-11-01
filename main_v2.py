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

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("LeonanGarcia.Nexo.v2")
        user32 = ctypes.windll.user32
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        LR_DEFAULTSIZE = 0x00000040
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1

        hicon = user32.LoadImageW(
            None,
            str(ICON_ICO),
            IMAGE_ICON,
            0,
            0,
            LR_LOADFROMFILE | LR_DEFAULTSIZE,
        )
        if not hicon:
            return

        for _ in range(30):
            hwnd = user32.FindWindowW(None, title)
            if hwnd:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                break
            time.sleep(0.1)
    except Exception:
        pass


def main():
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

    # Calcula dimensões ideais centralizadas na área de trabalho do Windows
    w, h = 1280, 800
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
            sw = rect.right - rect.left
            sh = rect.bottom - rect.top
            w = min(1280, int(sw * 0.95))
            h = min(800, int(sh * 0.85))
    except Exception:
        pass

    window = webview.create_window(
        "Nexo",
        base_url,
        width=w,
        height=h,
        min_size=(1000, 600),
        background_color="#F4F7FC",
        text_select=False,
    )

    def on_shown():
        threading.Thread(target=_set_windows_icon, args=("Nexo",), daemon=True).start()

    window.events.shown += on_shown
    webview.start(gui="edgechromium")
    server.should_exit = True


if __name__ == "__main__":
    main()
