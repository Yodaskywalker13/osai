# OSAI OS

> **Aviso:** Este projeto foi feito com Vibe Coding (programação assistida por IA).
> Revise o código e teste antes de uso em produção.

Central residencial de automação + assistente de IA local:
painel web de cômodos/dispositivos, chat com LLM (Ollama) e buscas web
em português (RAG via DuckDuckGo).

## Arquivos do projeto

| Arquivo / pasta | O que é |
|---|---|
| `OSAI_server.py` | Servidor FastAPI original (dashboard desktop) |
| `OSAI_desktop_app.py` | App desktop com janela nativa (pywebview) sobre o servidor |
| `OSAI_tvbox.py` | Servidor + **interface de TV Box** em `/tv` (D-pad) e detecção de TV na raiz — versão mais completa |
| `requirements.txt` | Dependências pinadas (FastAPI, uvicorn, pydantic, ollama, duckduckgo_search) |
| `Dockerfile` + `docker-compose.yml` | Imagem/serviço do core (porta 8000, Ollama no host via `host.docker.internal`) |
| `osai-os.spec` | Spec PyInstaller para gerar binário `osai-os` (janela nativa) |
| `osai-os-deb/` | Skeleton de pacote `.deb` (payload PyInstaller em `/usr/lib/osai-os`) |
| `osai-os_1.0.0_amd64.deb` | `.deb` já compilado |
| `dist/` + `build/` | Saídas do PyInstaller |
| `test_stress.py` | Bateria de testes de comandos contra o servidor |
| `README-TVBOX.md` | Documento da versão TVBox (servidor + TV) |
| `OSAI_flatpak/` | Empacotamento Flatpak (ver `OSAI_flatpak/README-FLATPAK.md`) |
| `android-tv/` | APK wrapper WebView para Android TV (ver `android-tv/README.md`) |

## Servidor

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Com Ollama rodando no host local:
python OSAI_server.py            # original
# ou:
python OSAI_tvbox.py             # com dashboard + /tv (recomendado)
```

Endpoints (iguais em todas as versões): `GET /`, `GET /tv`, `GET /api/estado`,
`POST /api/toggle`, `POST /api/comando`.

Env vars: `OLLAMA_HOST` (default `http://host.docker.internal:11434`) e,
na versão TVBox, `OSAI_UI` (`auto|tv|web`) e `OSAI_PORT` no flatpak.

## Docker

```bash
docker compose up -d        # core em 0.0.0.0:8000
```

## App desktop (janela nativa)

```bash
pip install pywebview
python OSAI_desktop_app.py
```

Abre janela `webview` apontada para `http://127.0.0.1:8000`, com o servidor
FastAPI em thread de fundo.

## Empacotamentos- **Flatpak**: `OSAI_flatpak/` → `./build-flatpak.sh` (detalhes no README do pacote)
- **TV Box**: `README-TVBOX.md` (browser TV Bro ou APK `android-tv/`)
- **Deb**: payload atual em `osai-os-deb/` + artefato `osai-os_1.0.0_amd64.deb`
- **PyInstaller**: `pyinstaller osai-os.spec`

## Testes

`test_stress.py` é da etapa antiga (**nota**: usa esquema antigo `/api/status` e
campo `"texto"` no POST; o servidor atual usa `/api/comando` com `"comando"`,
portanto precisa de ajuste antes de usar — pendência conhecida do refactor).

Para validar o servidor atual sem LLM real, chamada recomendada:

```curl
curl -X POST localhost:8000/api/toggle -H 'Content-Type: application/json' \
  -d '{"comodo":"quarto","dispositivo":"lampada_cabeceira"}'
```
