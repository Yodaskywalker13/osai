import os

os.environ.setdefault("OLLAMA_HOST", "http://127.0.0.1:11434")
os.environ.setdefault("OSAI_PORT", "8000")

import sys
import time
import threading
import urllib.request
import webbrowser

import uvicorn
import OSAI_tvbox as core

PORT = int(os.environ.get("OSAI_PORT", "8000"))
BASE = f"http://127.0.0.1:{PORT}"


def serve():
    uvicorn.run(core.app, host="0.0.0.0", port=PORT, log_level="warning")


def wait_ready(server_thread, timeout=30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not server_thread.is_alive():
            return False
        try:
            urllib.request.urlopen(f"{BASE}/api/estado", timeout=2)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def main():
    server_thread = threading.Thread(target=serve, daemon=True)
    server_thread.start()

    if not wait_ready(server_thread):
        print(f"[OSAI] Servidor nao subiu na porta {PORT}. Verifique conflitos (OSAI_PORT).", flush=True)
        sys.exit(1)

    print(f"[OSAI] Servidor online: {BASE} (dashboard) e {BASE}/tv (modo TV na rede)", flush=True)

    try:
        webbrowser.open(BASE + "/")
    except Exception:
        print("[OSAI] Sem ambiente grafico para abrir o navegador. Abra a URL acima manualmente.", flush=True)

    try:
        while server_thread.is_alive():
            time.sleep(60)
    except KeyboardInterrupt:
        print("[OSAI] Encerrando...", flush=True)
        sys.exit(0)


if __name__ == "__main__":
    main()
