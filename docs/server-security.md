# Server-Sicherheit (Netcup, Ubuntu 24.04, Docker)

Netcup-Server (VPS/Root-Server) sind **nicht verwaltet**: Netcup kümmert sich um Hardware und Netz, **Updates und
Absicherung des Betriebssystems liegen beim Kunden**. Diese Liste einmal abarbeiten, danach reicht ein Blick pro Monat.

Stand der Prüfung von außen (7.11.2026): nur Port 22, 80 und 443 offen · SSH für root nur mit Schlüssel ·
HTTPS mit gültigem Let's-Encrypt-Zertifikat (erneuert sich automatisch) · TLS 1.0/1.1 abgelehnt · Sicherheits-Header gesetzt.

Den aktuellen Zustand zeigt jederzeit (nur lesen, ändert nichts):

```bash
sudo bash tools/server_check.sh
```

## 1. Betriebssystem-Updates automatisch

Ubuntu bringt `unattended-upgrades` meist schon mit – prüfen und notfalls einschalten:

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades      # „Ja“ wählen
```

Kernel-Updates wirken erst nach einem Neustart. Automatisch nachts neu starten (die Container starten danach
von selbst wieder, `restart: unless-stopped`):

```bash
printf 'Unattended-Upgrade::Automatic-Reboot "true";\nUnattended-Upgrade::Automatic-Reboot-Time "04:30";\n' \
  | sudo tee /etc/apt/apt.conf.d/52optisense-reboot
sudo systemctl enable docker                          # Docker startet beim Booten
```

## 2. Docker-Images monatlich erneuern

Die Updates von Schritt 1 erreichen die Container **nicht**: Python, Debian im App-Image und Caddy werden nur beim
Neubauen aktuell. Einmal im Monat (und nach jedem Code-Update):

```bash
cd ~/OptiSense            # Projektordner auf dem Server
git pull
docker compose pull caddy
docker compose build --pull
docker compose up -d
docker image prune -f
```

## 3. SSH nur mit Schlüssel

Für root ist das schon so. Für alle Benutzer festschreiben – **vorher prüfen, dass die Anmeldung mit Schlüssel
klappt, und eine zweite SSH-Sitzung offen lassen**, bis der Test gelungen ist:

```bash
printf 'PasswordAuthentication no\nKbdInteractiveAuthentication no\nPermitRootLogin prohibit-password\n' \
  | sudo tee /etc/ssh/sshd_config.d/99-optisense.conf
sudo sshd -t && sudo systemctl reload ssh
```

Den privaten Schlüssel auf dem Laptop mit einer Passphrase schützen.

## 4. Firewall

Von außen sind heute nur 22, 80 und 443 erreichbar. Eine Firewall sorgt dafür, dass das so bleibt, wenn später
ein weiterer Dienst startet:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80,443/tcp
sudo ufw enable
```

Hinweis: Docker öffnet Ports, die in `docker-compose.yml` unter `ports:` stehen, an ufw vorbei. Dort stehen
absichtlich nur 80 und 443 (Caddy); die App-Container haben kein `ports:`.

`fail2ban` ist optional: Ohne Passwort-Anmeldung kann niemand Passwörter durchprobieren; es hält nur die Logs sauberer.

## 5. Netcup-Konten

- Kundenkonto (CCP) und Server-Panel (SCP): starkes Passwort und **Zwei-Faktor-Anmeldung** einschalten – wer das
  Panel hat, kann den Server neu installieren oder das Rescue-System starten.
- Vor größeren Änderungen im SCP einen **Snapshot** anlegen. OptiSense speichert keine Nutzerdaten (Sitzungen nur
  im Arbeitsspeicher); wichtig sind nur der Projektordner und die Datei `.env`.

## 6. Was die App selbst absichert

- **Datei-Upload (.lp):** Die Datei wird nur als Text gelesen (höchstens 20 KB, Caddy nimmt höchstens 1 MB an), auf
  Zahlen und Grenzen geprüft und nie gespeichert, ausgeführt oder an lp_solve weitergegeben. Der Upload-Pfad wird gegen
  Manipulation geprüft. Die Dateiendung spielt deshalb keine Rolle – auch eine umbenannte Programmdatei wäre nur Text,
  der nicht als Modell erkannt wird.
- **lp_solve** bekommt eine selbst erzeugte Datei mit Zahlen (ohne Texte der Nutzer), ohne Shell, mit 5 s Zeitlimit.
- **Container:** Die App läuft nicht als root und ist nur über Caddy erreichbar.
- **Browser:** HTTPS mit HSTS, Content-Security-Policy (keine fremden Skripte, keine Einbettung in fremde Seiten),
  Texte von Nutzern werden überall maskiert.
- **Pakete:** feste Versionen in `requirements.txt`; am 7.11.2026 mit `pip-audit` geprüft – keine bekannten Lücken.
  Bei Updates erneut prüfen: `pip install pip-audit && pip-audit -r requirements.txt`.

Restrisiko: Sehr viele gleichzeitige Verbindungen könnten den Server auslasten (kein Rate-Limit in Caddy).
Für den Einsatz in Lehrveranstaltungen ist das vertretbar; Netcup filtert grobe DDoS-Angriffe im Netz.
