#!/usr/bin/env bash
set -euo pipefail

APP_ID="os.osai.OS"
VERSION="1.0.0"
BRANCH="stable"

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$here"

command -v flatpak-builder >/dev/null 2>&1 || {
    echo "Instale: sudo apt/dnf pacotes: flatpak flatpak-builder" >&2
    exit 1
}

echo "[1/5] Instalando runtime/sdk do Flathub (apenas na primeira vez)"
flatpak install -y --or-update --system flathub \
    "org.freedesktop.Platform//26.08" \
    "org.freedesktop.Sdk//26.08"

echo "[2/5] Limpando build anterior"
rm -rf build repo

echo "[3/5] Compilando sandbox e instalando em ~/.local/share/flatpak (user)"
flatpak-builder \
    --user \
    --arch=x86_64 \
    --repo=repo \
    --force-clean \
    --state-dir=.flatpak-builder \
    build "${APP_ID}.json"

echo "[4/5] Instalando o app para o usuario atual"
flatpak install -y --user repo "${APP_ID}//${BRANCH}"

echo "[5/5] Gerando bundle distribuivel"
flatpak build-bundle repo "osai-os-${VERSION}-x86_64.flatpak" "${APP_ID}" "${BRANCH}"

echo
echo "Pronto! Opcoes para usar/distribuir:"
echo "  Executar:   flatpak run ${APP_ID}"
echo "  Instalar do bundle em outra maquina: flatpak install --user ./osai-os-${VERSION}-x86_64.flatpak"
echo "  (na outra maquina e preciso ter o runtime: flatpak install flathub org.freedesktop.Platform//26.08)"
