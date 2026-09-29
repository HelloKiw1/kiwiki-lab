#!/bin/bash

INTERVAL=300
LOG="/root/kiwiki-lab/auto-update.log"

echo "Kiwiki Auto Update iniciado." >> "$LOG"

while true; do
    echo "[$(date)] Verificando atualizacoes..." >> "$LOG"

    /root/kiwiki-lab/deploy/debian/update-kiwiki.sh \
        >> "$LOG" 2>&1

    echo >> "$LOG"

    sleep "$INTERVAL"
done

