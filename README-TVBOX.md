# OSAI OS - Versão TVBox (Android TV)

> **Aviso:** Este projeto foi feito com Vibe Coding (programação assistida por IA).
> Revise o código e teste antes de uso em produção.

Adaptação do OSAI OS Core para televisores / TV Boxes rodando Android TV, com
navegação **100% pelo controle remoto (D-pad)**.

## Arquitetura

```
+-----------------------------+         +---------------------------------+
|  PC / Docker / Termux       |  HTTP   |  TV Box (Smart TV)              |
|  OSAI_tvbox.py  (porta 8000)| <------>|  Browser (TV Bro) ou            |
|  + ollama + duckduckgo      |         |  APK "OSAI OS TV" (WebView)     |
+-----------------------------+         +---------------------------------+
```

O servidor **continua sendo o mesmo programa Python**. A diferença é a interface:
a rota `/tv` entrega uma "10-foot UI" em HTML puro (sem Tailwind, sem CDN, sem
Font Awesome), feita para webviews simples de TV Box e controlada pelo controle
remoto.

## O que mudou na versão TV

- **D-pad completo**: setas movem o foco geometricamente entre os elementos,
  `OK`/`Enter` liga/desliga dispositivos, envia chat e troca de abas.
- **Sem CDNs**: CSS e ícones (SVG inline) embutidos, funciona offline na rede local
  (exceto busca web/chat que dependem do servidor).
- **Fontes grandes e alto contraste** (10-foot UI), grid de 3 colunas de cômodos.
- **Auto-atualização** do estado a cada 5 s preservando o foco atual.
- **Detecção automática de TV**: acessando `/` com um User-Agent de TV
  ("Android TV", Fire TV `AFT*`, Chromecast `CrKey`, Shield, TV Box etc.) o
  servidor já entrega a UI de TV. Força via env: `OSAI_UI=tv` ou `OSAI_UI=web`.
- **API idêntica**: `/api/estado`, `/api/toggle`, `/api/comando` — o desktop
  (`/`) continua existindo com um botão extra "Modo TV Box".

## Como usar

### 1. Servidor (PC ou container, como já é hoje)

```bash
pip install -r requirements.txt
OLLAMA_HOST=http://192.168.1.105:11434 python OSAI_tvbox.py
# ou mantenho tudo igual ao docker-compose atual
```

Teste o modo TV já no navegador do PC: `http://localhost:8000/tv`
(e navegue com as setas do teclado — funciona igual ao controle).

### 2. TV Box — opção A (browser, mais rápido)

1. Instale **TV Bro** (browser open-source para TV, leve, com navegação por controle).
   Outra opção: navegador nativo da ROM ou "Puffin TV".
2. Abra `http://IP-DO-SERVIDOR:8000/tv` (salve como página inicial no TV Bro).

Dentro da webview do TV Bro o D-pad funciona direto (o JS captura as setas).

### 3. TV Box — opção B (APK próprio, ícone no launcher)

Projeto em `android-tv/` (wrapper WebView, sem dependências externas):

```bash
cd android-tv
# com Gradle instalado:
gradle assembleDebug
# APK em: app/build/outputs/apk/debug/app-debug.apk
# depois: adb install -r app/build/outputs/apk/debug/app-debug.apk
```

ou abra a pasta no Android Studio e use *Build > Build APK(s)*.

No primeiro uso o app pede o endereço do servidor (ex.: `http://192.168.1.105:8000`)
e abre `/tv`. Para trocar o endereço depois, aperte a tecla **MENU** do controle.

### 4. Servidor dentro da própria TV Box (Termux, opcional)

Se a box tiver Termux, só o **cliente** de Ollama roda nela (o Ollama fica no PC):

```bash
pkg install python
python -m venv osai && source osai/bin/activate
pip install fastapi uvicorn pydantic ollama duckduckgo-search
OLLAMA_HOST=http://192.168.1.105:11434 python OSAI_tvbox.py
```

e no browser/apk da própria box: `http://127.0.0.1:8000/tv`.

## Controles na TV

| Tecla do controle | Ação |
|---|---|
| Setas (D-pad) | Mover o foco (botões, devices, campo de texto) |
| OK / Enter | Ligar/desligar dispositivo, enviar mensagem, trocar aba |
| Aba "Assistente IA" | Foca no campo de texto e abre o teclado virtual |
| `0` | Atualizar mapa da casa |
| Voltar (na aba Assistente) | Volta para Casa Inteligente |
| MENU (no APK wrapper) | Configurar endereço do servidor |

## WiFi / rede

- TV Box e servidor precisam estar na mesma rede (ou acessível por IP).
- O APK usa `usesCleartextTraffic=true` para permitir `http://` na rede local.
- Se o firewall bloquear, libere a porta 8000 (e 11434 do Ollama se o chat
  rodar a partir de Termux/App de TV).
