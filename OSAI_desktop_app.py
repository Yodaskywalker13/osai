import sys
import threading
import uvicorn
import webview
from OSAI_server import app

def run_fastapi_server():
    """Sobe o servidor FastAPI localmente na porta 8000"""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == '__main__':
    # 1. Inicia o servidor FastAPI em uma thread separada em segundo plano
    server_thread = threading.Thread(target=run_fastapi_server, daemon=True)
    server_thread.start()

    # 2. Cria a janela nativa do Desktop integrada
    window = webview.create_window(
        title='OSAI OS — Control Center',
        url='http://127.0.0.1:8000',
        width=1280,
        height=800,
        min_size=(900, 600),
        resizable=True
    )

    # 3. Executa a aplicação webview
    webview.start()