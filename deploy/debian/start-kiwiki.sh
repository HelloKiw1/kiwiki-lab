#!/bin/bash

cd /root/kiwiki-lab || exit 1

# Kiwiki
if ! pgrep -f '[p]ython.*app.py' >/dev/null 2>&1; then
    nohup /root/kiwiki-lab/.venv/bin/python app.py \
        >> /root/kiwiki-lab/kiwiki.log 2>&1 &
fi

# Nginx permanece em primeiro plano para manter
# a sessão PRoot do Debian ativa.
exec nginx -g 'daemon off;'
