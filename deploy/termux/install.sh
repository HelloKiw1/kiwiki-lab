#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "== Kiwiki Lab - Termux installer =="

REPO="$1"

if [ -z "$REPO" ]; then
    echo "Uso:"
    echo "  bash install.sh CAMINHO_DO_REPOSITORIO"
    exit 1
fi

if [ ! -d "$REPO/deploy/termux" ]; then
    echo "Erro: deploy/termux nao encontrado em:"
    echo "  $REPO"
    exit 1
fi

echo "Instalando pacotes do Termux..."

pkg update -y

pkg install -y \
    git \
    openssh \
    curl \
    wget \
    nano \
    python \
    proot-distro \
    termux-api \
    iproute2

echo "Instalando Host Agent..."

cp "$REPO/deploy/termux/kiwiki-host-agent.py" \
   "$HOME/kiwiki-host-agent.py"

chmod +x "$HOME/kiwiki-host-agent.py"

echo "Configurando Termux:Boot..."

mkdir -p "$HOME/.termux/boot"

cp "$REPO/deploy/termux/20-kiwiki.sh" \
   "$HOME/.termux/boot/20-kiwiki.sh"

chmod +x "$HOME/.termux/boot/20-kiwiki.sh"

echo "Ativando wake lock..."

termux-wake-lock || true

echo "Iniciando SSH..."

if ! pgrep -x sshd >/dev/null 2>&1; then
    sshd
fi

echo
echo "Termux configurado."
echo
echo "Host Agent:"
echo "  $HOME/kiwiki-host-agent.py"
echo
echo "Boot:"
echo "  $HOME/.termux/boot/20-kiwiki.sh"
echo
echo "SSH:"
echo "  porta 8022"
