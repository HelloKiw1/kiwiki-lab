#!/bin/bash
set -e

echo "== Kiwiki Lab - Debian installer =="

REPO="/root/kiwiki-lab"

if [ ! -d "$REPO" ]; then
    echo "Erro: $REPO nao existe."
    exit 1
fi

apt update

apt install -y \
    git curl wget nano ca-certificates \
    python3 python3-pip python3-venv python3-dev \
    build-essential pkg-config libffi-dev libssl-dev \
    nginx sqlite3 procps iproute2 net-tools lsof

cd "$REPO"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

cp deploy/nginx/kiwiki.conf \
   /etc/nginx/sites-available/default

cp deploy/debian/start-kiwiki.sh \
   /root/start-kiwiki.sh

chmod +x /root/start-kiwiki.sh

nginx -t

echo
echo "Debian configurado."
echo "Teste com:"
echo "  /root/start-kiwiki.sh"
