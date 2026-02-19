# Schülersprecherwahl

Eine einfache Web-App zur Durchführung von Schülersprecherwahlen. Schüler scannen einen QR-Code oder geben einen Wahlcode ein und stimmen ab. Die Lehrkraft verwaltet alles über einen Admin-Bereich.

## Was die App kann

- Wahlen anlegen mit Kandidaten (inkl. Foto und Beschreibung)
- Wahlcodes als PDF mit QR-Codes generieren und ausdrucken
- Klassensätze verwalten (z.B. 7a: 25 Schüler, 7b: 29 Schüler) und Codes pro Klasse generieren
- Schulname auf den QR-Kärtchen und der Startseite anzeigen
- Anonyme Stimmabgabe (kein Rückschluss von Stimme auf Code möglich)
- Live-Ergebnisse mit Balkendiagramm im Admin-Bereich

## Voraussetzungen

Du brauchst einen Computer (oder Server) mit **Docker**. Docker ist ein Programm, das die App in einer Art "Container" laufen lässt, ohne dass du etwas installieren musst.

### Docker installieren

1. Gehe auf [docker.com/get-started](https://www.docker.com/get-started/) und lade **Docker Desktop** herunter
2. Installiere es (einfach den Anweisungen folgen)
3. Starte Docker Desktop

Ob Docker läuft, kannst du testen, indem du ein Terminal öffnest und eingibst:

```
docker --version
```

Wenn eine Versionsnummer erscheint, ist alles bereit.

## App starten

### 1. Projektordner öffnen

Öffne ein Terminal und navigiere in den Projektordner:

```
cd pfad/zum/schuelerwahl
```

### 2. Umgebungsvariablen setzen

Erstelle im Projektordner eine Datei namens `.env` mit folgendem Inhalt:

```
SECRET_KEY=ein-langes-zufaelliges-passwort-hier
ADMIN_PASSWORD=dein-admin-passwort
BASE_URL=http://localhost
```

- **SECRET_KEY**: Ein beliebiger langer Text (z.B. `meine-schule-wahl-2026-geheim`). Wird intern zur Absicherung verwendet.
- **ADMIN_PASSWORD**: Das Passwort, mit dem du dich im Admin-Bereich anmeldest.
- **BASE_URL**: Die Adresse, unter der die App erreichbar ist. Auf deinem Rechner: `http://localhost`. Auf einem Server mit eigener Domain: z.B. `https://wahl.meine-schule.de`.

### 3. App starten

Im Terminal eingeben:

```
docker compose up -d
```

Das wars! Die App läuft jetzt. Beim ersten Start werden alle notwendigen Komponenten automatisch heruntergeladen (dauert 1-2 Minuten, danach startet alles sofort).

### 4. App öffnen

Öffne im Browser: **http://localhost**

## Benutzung

### Admin-Bereich

1. Gehe auf **http://localhost/admin/login**
2. Melde dich mit dem Passwort aus der `.env`-Datei an
3. Erstelle eine neue Wahl (Name, Schulname, Jahr, max. Stimmen)
4. Füge Kandidaten hinzu (mit Foto und Beschreibung)
5. Gehe auf **Codes** und füge Klassen hinzu (z.B. "7a" mit 25 Schülern)
6. Klicke auf **Codes für alle Klassen generieren**
7. Lade das **PDF herunter** und drucke es aus
8. Aktiviere die Wahl (grüner "Aktivieren"-Button)

### Wahl durchführen

1. Schneide die QR-Code-Kärtchen aus (das PDF hat Schnittlinien)
2. Verteile je ein Kärtchen pro Schüler
3. Schüler scannen den QR-Code mit dem Handy oder geben den Code manuell ein
4. Schüler wählen ihre Kandidaten und bestätigen
5. Ergebnisse sind live im Admin-Bereich unter **Ergebnisse** sichtbar

### Tipps

- Die Codes im PDF sind nach Klassen sortiert mit Seitenumbruch pro Klasse, so lassen sie sich einfach verteilen
- Zusätzlich zu den Klassencodes kannst du Reservecodes ohne Klassenzuordnung generieren
- Jeder Code funktioniert nur einmal
- Im Admin-Bereich siehst du, welche Codes bereits verwendet wurden

## App stoppen

```
docker compose down
```

Die Daten (Wahlen, Stimmen, Codes) bleiben erhalten und sind beim nächsten Start wieder da.

## Auf einem Server betreiben

Wenn du die App nicht nur lokal, sondern im Schulnetzwerk oder im Internet betreiben willst:

1. Installiere Docker auf dem Server
2. Kopiere den Projektordner auf den Server
3. Passe in der `.env`-Datei die `BASE_URL` an deine Domain an (z.B. `https://wahl.meine-schule.de`)
4. Passe in `nginx/nginx.conf` den `server_name` an deine Domain an
5. Starte die App mit `docker compose up -d`
6. Für HTTPS mit eigenem Zertifikat (Let's Encrypt) einmalig ausführen:
   ```
   docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d wahl.meine-schule.de
   ```
   Danach nginx neu starten: `docker compose restart nginx`

## Ohne Docker starten (für Entwickler)

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Die App läuft dann auf **http://localhost:5000**.
