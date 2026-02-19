# Schülersprecherwahl

Eine einfache Web-App zur Durchführung von Schülersprecherwahlen. Schüler scannen einen QR-Code oder geben einen Wahlcode ein und stimmen ab. Die Lehrkraft verwaltet alles über einen Admin-Bereich.

## Was die App kann

- **Schuleinstellungen**: Schulname und Logo zentral verwalten (wird auf Startseite, Abstimmungsseite und QR-Kärtchen angezeigt)
- **Wahlen anlegen** mit Kandidaten (inkl. Foto und Beschreibung)
- **Klassensätze verwalten** (z.B. 7a: 25 Schüler, 7b: 29 Schüler) und Codes pro Klasse generieren
- **Wahlcodes als PDF** mit QR-Codes generieren und ausdrucken (nach Klassen sortiert, Seitenumbruch pro Klasse)
- **Reservecodes** ohne Klassenzuordnung generieren (separates PDF)
- **Anonyme Stimmabgabe** (kein Rückschluss von Stimme auf Code möglich)
- **Live-Ergebnisse** mit Balkendiagramm im Admin-Bereich
- **Präsentationsmodus**: Vollbild-Ansicht mit dunklem Design, Live-Balkendiagramm, Fortschrittsbalken und Sound bei neuen Stimmen (ideal für Beamer)
- **Wahl beenden**: Wahl offiziell abschließen, alle unbenutzten Codes werden ungültig

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
3. Richte unter **Schuleinstellungen** den Schulnamen und optional ein Logo ein
4. Erstelle eine neue Wahl (Name, Jahr, max. Stimmen)
5. Füge Kandidaten hinzu (mit Foto und Beschreibung)
6. Gehe auf **Codes** und füge Klassen hinzu (z.B. "7a" mit 25 Schülern)
7. Klicke auf **Codes für alle Klassen generieren**
8. Lade das **PDF herunter** und drucke es aus
9. Optional: Generiere zusätzlich Reservecodes ohne Klasse
10. Aktiviere die Wahl (grüner "Aktivieren"-Button)

### Wahl durchführen

1. Schneide die QR-Code-Kärtchen aus (das PDF hat Schnittlinien)
2. Verteile je ein Kärtchen pro Schüler
3. Schüler scannen den QR-Code mit dem Handy oder geben den Code manuell ein
4. Schüler wählen ihre Kandidaten und bestätigen
5. Ergebnisse sind live im Admin-Bereich unter **Ergebnisse** sichtbar
6. Nutze den **Präsentationsmodus** (Button im Dashboard), um Ergebnisse per Beamer zu zeigen

### Wahl beenden

Wenn die Abstimmung abgeschlossen ist:

1. Gehe auf **Bearbeiten** der Wahl
2. Klicke auf **Wahl beenden**
3. Bestätige die Warnung (alle unbenutzten Codes werden ungültig)
4. Die offiziellen Ergebnisse mit Wahlbeteiligung werden angezeigt

### Tipps

- Die Codes im PDF sind nach Klassen sortiert mit Seitenumbruch pro Klasse, so lassen sie sich einfach verteilen
- Einzelne Klassen-PDFs können direkt in der Klassentabelle heruntergeladen werden
- Reservecodes (ohne Klasse) haben ein eigenes PDF
- Jeder Code funktioniert nur einmal
- Im Admin-Bereich siehst du, welche Codes bereits verwendet wurden
- Die Buttons "Ergebnisse" und "Präsentation" erscheinen im Dashboard erst, nachdem die Wahl erstmalig aktiviert wurde

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
