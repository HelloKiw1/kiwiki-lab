# Kiwiki Lab - Deploy Android

Este diretorio contem os arquivos usados para executar o Kiwiki Lab em um smartphone Android com Termux + Debian via PRoot.

## Arquitetura

Android
- Tailscale
- Termux
  - SSH: 8022
  - Host Agent: 9100
  - Termux:Boot
- Debian 12 via PRoot
  - Kiwiki Lab / Flask: 5000
  - Nginx: 8080

## Ambiente atual

- Dispositivo: Xiaomi M2006C3LII
- Device: dandelion
- Android: 10
- Termux: ARM 32 bits
- Debian: 12 Bookworm
- Debian architecture: armhf
- Python: 3.11

## Preparar Termux

pkg update && pkg upgrade -y

pkg install -y git openssh curl wget nano python proot-distro termux-api iproute2

termux-setup-storage
termux-wake-lock
passwd
sshd

## Instalar Debian

proot-distro install debian:12 --name debian --architecture arm

proot-distro login debian

## Instalar Kiwiki Lab

cd /root

git clone https://github.com/HelloKiw1/kiwiki-lab.git

cd kiwiki-lab

python3 -m venv .venv

source .venv/bin/activate

python -m pip install --upgrade pip

python -m pip install -r requirements.txt

## Nginx

cp deploy/nginx/kiwiki.conf /etc/nginx/sites-available/default

nginx -t

## Inicializador Debian

cp deploy/debian/start-kiwiki.sh /root/start-kiwiki.sh

chmod +x /root/start-kiwiki.sh

## Host Agent

Arquivo:

deploy/termux/kiwiki-host-agent.py

Endpoint:

http://127.0.0.1:9100/status

## Termux Boot

Arquivo:

deploy/termux/20-kiwiki.sh

## Testes

curl -s http://127.0.0.1:9100/status

curl -I http://127.0.0.1:5000

curl -I http://127.0.0.1:8080

## Portas

5000 - Kiwiki Lab / Flask
8000 - Django / Codex
8080 - Nginx
8022 - SSH Termux
9100 - Kiwiki Host Agent
5432 - PostgreSQL
3306 - MySQL / MariaDB
6379 - Redis

## Seguranca

Nunca salvar no repositorio:

- Personal Access Tokens
- senhas
- chaves SSH privadas
- arquivos .env com credenciais
