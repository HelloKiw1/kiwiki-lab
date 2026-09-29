#!/bin/bash
set -e

REPO="/root/kiwiki-lab"
BRANCH="main"

cd "$REPO"

echo "== Kiwiki Lab Updater =="

if [ -n "$(git status --porcelain)" ]; then
    echo "ERRO: existem alteracoes locais."
    echo "Atualizacao cancelada para evitar perda de arquivos."
    git status --short
    exit 1
fi

echo "Verificando GitHub..."

git fetch origin "$BRANCH"

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "Kiwiki ja esta atualizado."
    exit 0
fi

echo "Nova versao encontrada."

CHANGED=$(git diff --name-only "$LOCAL" "$REMOTE")

git pull --ff-only origin "$BRANCH"

if echo "$CHANGED" | grep -qx "requirements.txt"; then
    echo "Atualizando dependencias Python..."
    .venv/bin/python -m pip install -r requirements.txt
fi

echo "Reiniciando Kiwiki..."

pkill -f '/root/kiwiki-lab/.venv/bin/python app.py' 2>/dev/null || true

sleep 2

nohup /root/kiwiki-lab/.venv/bin/python app.py \
    >> /root/kiwiki-lab/kiwiki.log 2>&1 &

sleep 3

if curl -fsS http://127.0.0.1:5000/api/status >/dev/null; then
    echo "Kiwiki atualizado e funcionando."
else
    echo "AVISO: atualizacao concluida, mas o teste HTTP falhou."
    exit 1
fi
