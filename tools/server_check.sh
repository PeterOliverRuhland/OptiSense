#!/usr/bin/env bash
# Sicherheits-Check fuer den OptiSense-Server – liest nur, aendert nichts.
# Aufruf auf dem Server (im Projektordner):  sudo bash tools/server_check.sh
# Was die Werte bedeuten und wie man sie einstellt: docs/server-security.md
set -u
h() { printf '\n== %s\n' "$1"; }

h "System"
. /etc/os-release && echo "$PRETTY_NAME"
echo "Kernel: $(uname -r)  |  laeuft seit: $(uptime -p)"

h "Ausstehende Updates"
apt-get update -qq >/dev/null 2>&1
echo "Pakete mit Updates: $(apt list --upgradable 2>/dev/null | tail -n +2 | wc -l)"
echo "davon Sicherheitsupdates: $(apt list --upgradable 2>/dev/null | grep -c -- '-security')"

h "Neustart noetig?"
if [ -f /var/run/reboot-required ]; then cat /var/run/reboot-required; else echo "nein"; fi

h "Automatische Sicherheitsupdates (unattended-upgrades)"
echo "Dienst: $(systemctl is-enabled unattended-upgrades 2>&1) / $(systemctl is-active unattended-upgrades 2>&1)"
cat /etc/apt/apt.conf.d/20auto-upgrades 2>/dev/null || echo "20auto-upgrades fehlt"
grep -rhE '^\s*Unattended-Upgrade::Automatic-Reboot' /etc/apt/apt.conf.d/ 2>/dev/null || echo "Automatic-Reboot: nicht gesetzt (Standard: kein automatischer Neustart)"
echo "letzte Laeufe:"; tail -n 3 /var/log/unattended-upgrades/unattended-upgrades.log 2>/dev/null || echo "  kein Log gefunden"

h "SSH (wirksame Einstellungen)"
sshd -T 2>/dev/null | grep -E '^(port|permitrootlogin|passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication|maxauthtries) '
echo "fehlgeschlagene Anmeldeversuche (24 h): $(journalctl -u ssh -u sshd --since '24 hours ago' 2>/dev/null | grep -c -i -E 'failed|invalid user')"

h "Dienste, die auf Verbindungen warten"
ss -tulpn | awk 'NR == 1 || /LISTEN/'

h "Firewall (ufw)"
ufw status verbose 2>&1 | head -20

h "fail2ban"
echo "Dienst: $(systemctl is-active fail2ban 2>&1)"

h "Docker"
docker --version
docker compose version 2>/dev/null
echo "Docker startet beim Booten: $(systemctl is-enabled docker 2>&1)"
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'

h "Alter der Images (aelter als ~1 Monat: neu bauen, siehe docs/server-security.md)"
docker images --format 'table {{.Repository}}:{{.Tag}}\t{{.CreatedSince}}'

h "Speicherplatz"
df -h / | tail -1
