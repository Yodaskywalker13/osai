# OSAI OS - Versao Flatpak

> **Aviso:** Este projeto foi feito com Vibe Coding (programação assistida por IA).
> Revise o código e teste antes de uso em produção.

Empacotamento em Flatpak do **OSAI OS Core** para Linux desktop. O app sobe o
servidor FastAPI dentro do sandbox, abre o painel no navegador e ainda serve a
**interface de TV Box** (`/tv`) para toda a rede local — igual ao docker-compose.

## Conteudo

```
OSAI_flatpak/
  os.osai.OS.json        manifest do Flatpak
  build-flatpak.sh       build + install + gerar bundle .flatpak
  src/
    OSAI_tvbox.py        servidor (dashboard desktop + /tv)
    osai_main.py         entrypoint: thread uvicorn + abrir navegador
    requirements.txt     dependencias (pinadas, do repo)
  app/
    osai-os-launcher.sh  launcher em /app/bin/osai-os
    os.osai.OS.desktop   entrada no menu de aplicativos
    os.osai.OS.metainfo.xml  AppStream (para lojas/GNOME Software)
    icons/hicolor/...    icone 64/128/256/512
```

## Pré-requisitos

```bash
# Debian/Ubuntu
sudo apt install flatpak flatpak-builder
# Fedora
sudo dnf install flatpak flatpak-builder

flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.repo
```

## Build e install

```bash
cd OSAI_flatpak
chmod +x build-flatpak.sh
./build-flatpak.sh
```

O script instala o runtime org.freedesktop 24.08 (só na primeira vez), compila
tudo (Python + dependencias do `requirements.txt` vão para /app via pip), executa
`flatpak install --user` e gera o bundle distribuivel:

```
osai-os-1.0.0-x86_64.flatpak
```

### Distribuir

Em outra maquina (com o runtime presente):

```bash
flatpak install flathub org.freedesktop.Platform//24.08
flatpak install --user ./osai-os-1.0.0-x86_64.flatpak
flatpak run os.osai.OS
```

## Uso

- Menu de aplicativos: **OSAI OS** — abre o painel em `http://127.0.0.1:8000`.
- Terminal: `flatpak run os.osai.OS` (logs visíveis).
- TV Box na mesma rede: navegue até `http://IP-DO-PC:8000/tv`
  (o servidor escuta em 0.0.0.0 dentro do sandbox porque o app tem
  `--share=network`).

## Ollama

O Ollama **não** vem dentro do flatpak (roda no host). O sandbox compartilha a
rede do host, então `http://127.0.0.1:11434` já funciona por padrão.

Para apontar outro host:

```bash
flatpak override --user --env=OLLAMA_HOST=http://192.168.1.105:11434 os.osai.OS
```

## Porta e variáveis

| Variavel     | Default | Como mudar                                             |
|--------------|---------|--------------------------------------------------------|
| `OSAI_PORT`  | 8000    | `flatpak override --user --env=OSAI_PORT=8010 os.osai.OS` |
| `OLLAMA_HOST`| 127.0.0.1:11434 | `flatpak override --user --env=...`            |

Ou na execução: `flatpak run --env=OSAI_PORT=8010 os.osai.OS`

## Notas

- Arquitetura alvo: x86_64 (`only-arches` no manifest).
- O app aparece na loja (GNOME Software) com o AppStream `os.osai.OS.metainfo.xml`.
- Para publicar no Flathub, suba o repo gerado: `flatpak build-update-repo --gpg-sign=... repo` (Index incluido em `repo/appstream/x86_64/active/iso-scan/appstream.xml.gz`).
- Desktop file usa `Exec=osai-os` e `Icon=os.osai.OS`, instalados no prefixo /app do sandbox.
