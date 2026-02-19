# Schülersprecherwahl

Eine Web-App, mit der Schulen eine Schülersprecherwahl digital durchführen können.
Die Schüler stimmen per Smartphone ab, die Lehrkraft verwaltet alles über einen geschützten Verwaltungsbereich.

---

## So funktioniert es

1. Die Lehrkraft legt eine Wahl an und trägt die Kandidaten ein
2. Für jede Klasse werden Wahlzettel mit QR-Codes als PDF erzeugt und ausgedruckt
3. Jeder Schüler bekommt einen Zettel, scannt den QR-Code mit dem Handy und stimmt ab
4. Die Ergebnisse sind sofort live im Verwaltungsbereich sichtbar
5. Am Ende wird die Wahl offiziell beendet

Die Abstimmung ist **anonym** -- es ist technisch nicht möglich, eine Stimme einem bestimmten Code zuzuordnen.

---

## Funktionen im Überblick

| Funktion | Beschreibung |
|---|---|
| **Kandidaten** | Name, Klasse, Beschreibung und Foto pro Kandidat |
| **Klassenverwaltung** | Klassen mit Schülerzahl anlegen (z.B. "7a" mit 25 Schülern) |
| **QR-Code-Kärtchen** | PDF mit QR-Codes und Wahlcodes zum Ausdrucken und Ausschneiden |
| **Klassensätze** | Codes nach Klassen getrennt generieren; jede Klasse beginnt im PDF auf einer neuen Seite |
| **Reservecodes** | Zusätzliche Codes ohne Klassenzuordnung (z.B. für Nachzügler) |
| **Schulbranding** | Schulname und Logo auf der Startseite, der Abstimmungsseite und den QR-Kärtchen |
| **Live-Ergebnisse** | Balkendiagramm mit automatischer Aktualisierung alle 5 Sekunden |
| **Präsentationsmodus** | Vollbild-Ansicht mit dunklem Hintergrund, ideal zur Anzeige per Beamer; mit Fortschrittsbalken und akustischem Signal bei neuen Stimmen |
| **Wahl beenden** | Wahl offiziell abschließen; alle noch nicht verwendeten Codes werden automatisch ungültig |
| **Sicherheit** | Jeder Code funktioniert nur einmal; Schutz gegen Brute-Force-Angriffe; anonyme Stimmabgabe |

---

## Voraussetzungen

Die App wird über **Docker** betrieben. Docker sorgt dafür, dass alles automatisch eingerichtet wird -- man muss nichts selbst installieren oder konfigurieren.

### Docker installieren

1. **Docker Desktop** herunterladen: [docker.com/get-started](https://www.docker.com/get-started/)
2. Installieren (einfach den Anweisungen auf dem Bildschirm folgen)
3. Docker Desktop starten

Zur Kontrolle ein Terminal (Mac: "Terminal", Windows: "Eingabeaufforderung") öffnen und eintippen:

```
docker --version
```

Wenn eine Versionsnummer erscheint (z.B. `Docker version 27.5.1`), ist Docker bereit.

---

## Einrichtung (einmalig)

### 1. Projektordner herunterladen

Den Projektordner `schuelerwahl` auf den Computer laden (z.B. in den Downloads-Ordner).

### 2. Einstellungsdatei anlegen

Im Projektordner eine neue Textdatei mit dem Namen `.env` erstellen (der Punkt am Anfang ist wichtig!) und folgendes eintragen:

```
SECRET_KEY=ein-langer-zufaelliger-text-z-b-schule2026geheim
ADMIN_PASSWORD=mein-sicheres-passwort
BASE_URL=http://localhost
```

**Was bedeuten diese Einstellungen?**

| Einstellung | Erklärung |
|---|---|
| `SECRET_KEY` | Ein beliebig langer Text, der die App intern absichert. Kann irgendetwas sein, z.B. `meine-schule-wahl-2026-xyz`. |
| `ADMIN_PASSWORD` | Das Passwort für den Verwaltungsbereich. Dieses Passwort gibt man ein, um Wahlen zu verwalten. |
| `BASE_URL` | Die Adresse, unter der die App erreichbar ist. Am eigenen Rechner: `http://localhost`. Auf einem Server: z.B. `https://wahl.meine-schule.de`. |

### 3. App starten

Terminal öffnen, in den Projektordner wechseln und eingeben:

```
cd pfad/zum/schuelerwahl
docker compose up -d
```

Beim allerersten Start lädt Docker die benötigten Komponenten herunter (1-2 Minuten). Danach startet die App sofort.

### 4. Im Browser öffnen

Die Seite der Schüler: **http://localhost**
Der Verwaltungsbereich: **http://localhost/admin/login**

---

## Anleitung: Wahl vorbereiten

### Schritt 1: Anmelden

Im Browser **http://localhost/admin/login** aufrufen und das Passwort aus der `.env`-Datei eingeben.

### Schritt 2: Schuleinstellungen

Ganz oben im Verwaltungsbereich den **Schulnamen** eintragen (z.B. "Realschule Bobingen"). Optional kann auch ein **Schullogo** hochgeladen werden (Bilddatei, z.B. PNG oder JPG). Beides erscheint dann auf der Startseite, der Abstimmungsseite und auf den ausgedruckten QR-Kärtchen.

### Schritt 3: Wahl erstellen

Unter "Neue Wahl erstellen" ausfüllen:

- **Name**: z.B. "Schülersprecherwahl"
- **Jahr**: z.B. 2026
- **Max. Stimmen**: Wie viele Kandidaten jeder Schüler wählen darf (z.B. 3)

Auf **Erstellen** klicken.

### Schritt 4: Kandidaten eintragen

Auf der Seite der neuen Wahl die Kandidaten hinzufügen. Für jeden Kandidaten kann man eingeben:

- **Name** (Pflichtfeld)
- **Klasse** (optional, z.B. "10a")
- **Beschreibung** (optional, z.B. eine kurze Vorstellung)
- **Foto** (optional, z.B. ein Portraitfoto)

### Schritt 5: Klassen anlegen und Codes erzeugen

Im Verwaltungsbereich auf **Codes** klicken. Dort zuerst die Klassen eintragen:

1. Klassenname eingeben (z.B. "5a") und die Schülerzahl (z.B. 25)
2. Auf **Klasse hinzufügen** klicken
3. Diesen Vorgang für alle Klassen wiederholen

Anschließend auf **Codes für alle Klassen generieren** klicken. Die App erzeugt für jede Klasse genau so viele Codes wie Schüler eingetragen sind.

**Tipp:** Zusätzlich können im Bereich "Reservecodes" weitere Codes ohne Klassenzuordnung erstellt werden -- z.B. für Nachzügler oder falls ein Zettel verloren geht.

### Schritt 6: PDF herunterladen und ausdrucken

Nach dem Generieren erscheint der Button **PDF herunterladen**. Das PDF enthält Kärtchen mit QR-Codes und Wahlcodes zum Ausschneiden.

Wichtig zu wissen:
- Jede Klasse beginnt auf einer **neuen Seite** -- so lassen sich die Zettel leicht klassenweise verteilen
- Die Klassen sind von der niedrigsten zur höchsten Jahrgangsstufe sortiert (5a, 5b, 6a, ... 10d)
- Einzelne Klassen-PDFs können auch separat über den **PDF**-Link in der Klassentabelle heruntergeladen werden
- Reservecodes haben ein eigenes PDF

### Schritt 7: Wahl aktivieren

Zurück auf der Seite der Wahl (Button **Bearbeiten** im Dashboard) den grünen Button **Aktivieren** klicken. Die Wahl ist jetzt aktiv und Schüler können abstimmen.

Hinweis: Eine Wahl kann erst aktiviert werden, wenn mindestens Codes erzeugt wurden.

---

## Anleitung: Wahltag

### Ablauf für die Schüler

1. Jeder Schüler bekommt ein Kärtchen mit einem QR-Code
2. QR-Code mit der Handy-Kamera scannen (oder die Adresse öffnen und den Code manuell eingeben)
3. Kandidaten auswählen und auf **Stimme abgeben** tippen
4. Auswahl im Bestätigungsdialog nochmals prüfen und auf **Bestätigen** tippen
5. Fertig -- das Kärtchen kann eingesammelt werden

Jeder Code funktioniert **nur einmal**. Wenn ein Code bereits verwendet wurde, erscheint eine entsprechende Meldung.

### Ergebnisse verfolgen

Während der Wahl können die Ergebnisse live verfolgt werden. Im Dashboard erscheinen nach der erstmaligen Aktivierung zwei neue Buttons:

- **Ergebnisse**: Zeigt ein Balkendiagramm und eine Rangliste mit Wahlbeteiligung
- **Präsentation**: Vollbild-Ansicht für den Beamer mit dunklem Hintergrund, Live-Fortschrittsbalken und einem akustischen Signal bei jeder neuen Stimme (Sound kann ausgeschaltet werden)

### Wahl beenden

Wenn alle Schüler abgestimmt haben:

1. Im Dashboard auf **Bearbeiten** klicken
2. Den orangen Button **Wahl beenden** klicken
3. Die Sicherheitsabfrage bestätigen

Beim Beenden passiert Folgendes:
- Die Wahl wird deaktiviert (es kann niemand mehr abstimmen)
- Alle noch nicht verwendeten Codes werden automatisch ungültig gemacht
- Die Ergebnisseite zeigt ab jetzt "Offizielle Ergebnisse" an

Dieser Vorgang kann **nicht rückgängig** gemacht werden.

---

## App stoppen und wieder starten

### Stoppen

```
docker compose down
```

### Wieder starten

```
docker compose up -d
```

Alle Daten (Wahlen, Stimmen, Kandidaten, Codes) bleiben erhalten. Sie werden erst gelöscht, wenn man eine Wahl im Verwaltungsbereich manuell löscht.

---

## Betrieb auf einem Server (z.B. für das ganze Schulnetzwerk)

Wenn die App nicht nur auf einem einzelnen Rechner, sondern schulweit über das Netzwerk oder Internet erreichbar sein soll:

1. Einen Server mieten (z.B. Hetzner CX22 oder CX23, ab ca. 4 Euro/Monat) und Docker dort installieren
2. Den Projektordner auf den Server kopieren
3. In der `.env`-Datei die `BASE_URL` anpassen (z.B. `https://wahl.meine-schule.de`)
4. In der Datei `nginx/nginx.conf` den `server_name` auf die eigene Domain ändern (an beiden Stellen, wo `wahl.example.de` steht)
5. Die App starten: `docker compose up -d`
6. Für eine verschlüsselte Verbindung (HTTPS) einmalig ausführen:
   ```
   docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d wahl.meine-schule.de
   ```
   Danach: `docker compose restart nginx`

---

## Häufige Fragen

**Können Schüler mehrfach abstimmen?**
Nein. Jeder Code kann nur einmal verwendet werden. Es ist nicht möglich, denselben Code zweimal einzusetzen.

**Kann man sehen, wer wen gewählt hat?**
Nein. Die Stimmabgabe ist anonym. Technisch wird keine Verbindung zwischen dem Code und der abgegebenen Stimme gespeichert.

**Was passiert, wenn ein Schüler seinen Zettel verliert?**
Dafür gibt es die Reservecodes. Im Verwaltungsbereich unter "Codes" können jederzeit zusätzliche Codes ohne Klassenzuordnung erzeugt werden.

**Kann man die Wahl nach dem Beenden wieder öffnen?**
Nein. Sobald eine Wahl beendet wurde, ist das endgültig. Bei Bedarf kann eine neue Wahl angelegt werden.

**Wie viele Schüler kann die App gleichzeitig bedienen?**
Auf einem kleinen Server (z.B. Hetzner CX23) problemlos mehrere hundert gleichzeitige Nutzer.

**Brauchen die Schüler eine App?**
Nein. Die Abstimmung funktioniert komplett im Browser -- auf jedem Smartphone, Tablet oder Computer.

---

## Für Entwickler

Die App ohne Docker direkt starten:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Die App läuft dann auf **http://localhost:5050** (Entwicklungsmodus).

Verwendete Technologien: Python, Flask, SQLite, Tailwind CSS, Chart.js, ReportLab (PDF), qrcode (QR-Codes).
