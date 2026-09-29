#!/data/data/com.termux/files/usr/bin/bash

# Dá alguns segundos para o Android terminar o boot.
sleep 15

termux-wake-lock

# SSH
if ! pgrep -x sshd >/dev/null 2>&1; then
    sshd
fi

# Host Agent Android
if ! pgrep -f '[k]iwiki-host-agent.py' >/dev/null 2>&1; then
    nohup python "$HOME/kiwiki-host-agent.py" \
        >> "$HOME/kiwiki-host-agent.log" 2>&1 &
fi

# Debian + Kiwiki + Nginx
if ! pgrep -f '[p]root-distro.*login debian.*start-kiwiki' >/dev/null 2>&1; then
    nohup proot-distro login debian -- /root/start-kiwiki.sh \
        >> "$HOME/kiwiki-debian.log" 2>&1 &
fi
