# Meeting to Protocol

## 1. Übersicht

Dieses Projekt wandelt Audio-Aufzeichnungen von Meetings automatisch in ein strukturiertes, transkribiertes und zusammengefasstes Protokoll um. Es nutzt modernste KI-Modelle für Sprecher-Erkennung (Diarisierung), Transkription und Zusammenfassung.

Das Projekt ist für zwei Hauptanwendungsfälle konzipiert:

*   **Als einfach zu bedienende Desktop-Anwendung:** Eine einzelne ausführbare Datei für Windows und macOS/Linux, die keine Installation oder technisches Wissen erfordert. Perfekt für Endanwender.
*   **Als robuster Microservice:** Eine API-Schnittstelle, die es Entwicklern ermöglicht, die Analysefunktionen in andere Anwendungen (z.B. das "DreamMall"-Projekt) zu integrieren.

![Screenshot der neuen Oberfläche](docs/screenshot.png) <!-- Platzhalter für einen zukünftigen Screenshot -->

## 2. Für Endanwender: Desktop-Anwendung

Für die einfachste Nutzung können Sie die fertige Anwendung für Ihr Betriebssystem von der [Releases-Seite](https-platzhalter-github-releases) herunterladen. Es ist keine Installation von Python oder anderen Werkzeugen notwendig.

1.  Laden Sie die Datei für Ihr Betriebssystem (z.B. `MeetingProtocolGenerator.exe` für Windows) herunter.
2.  Doppelklicken Sie die Datei, um die Anwendung zu starten.
3.  Im Programmfenster können Sie Ihre API-Schlüssel für OpenAI/HuggingFace hinterlegen (optional, nur für Zusammenfassungen benötigt).
4.  Laden Sie eine Audiodatei hoch und starten Sie die Analyse.

## 3. Für Entwickler

### 3.1. Architektur

*   **Backend (`app.py`):** Ein Flask-basierter Microservice, der die API-Endpunkte bereitstellt (`/process`, `/status`, `/results`, `/summarize`).
*   **Analyse-Logik (`processing.py`):** Nutzt `pyannote.audio` für die Diarisierung und `openai-whisper` für die Transkription. `ffmpeg` wird automatisch über `imageio-ffmpeg` mitgeliefert.
*   **Zusammenfassungs-Logik (`summarizer.py`):** Kapselt die Anbindung an OpenAI-, HuggingFace- und lokale Ollama-Modelle.
*   **GUI-Startpunkt (`gui.py`):** Dient als Einstiegspunkt für die Desktop-Anwendung. Es startet den Flask-Server und zeigt das Frontend in einem `pywebview`-Fenster an.
*   **Frontend (`templates/index.html`):** Eine moderne Single-Page-Anwendung mit HTML, Pico.css und JavaScript, die als Benutzeroberfläche dient.

### 3.2. Setup aus dem Quellcode

**Voraussetzungen:**
*   Python 3.9+
*   Git

**Schritte:**
1.  **Repository klonen:**
    ```bash
    git clone https://github.com/ogerly/Meeting-to-Protocol.git
    cd Meeting-to-Protocol
    ```
2.  **Abhängigkeiten installieren:**
    Das `setup.sh`-Skript erstellt eine virtuelle Umgebung und installiert alle notwendigen Pakete.
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```
3.  **Umgebungsvariablen einrichten (für Microservice):**
    Erstellen Sie eine `.env`-Datei für Ihre API-Schlüssel. Diese werden vom Microservice verwendet.
    ```bash
    cp env .env
    # Bearbeiten Sie .env und fügen Sie Ihre Schlüssel hinzu
    ```

### 3.4. Anwendung starten

Sie können die Anwendung in zwei verschiedenen Modi starten:

**Modus A: Als Desktop-Anwendung (mit GUI)**
Dieser Modus ist ideal für die lokale Nutzung und zum Testen des Frontends.
```bash
source venv/bin/activate
python gui.py
```

**Modus B: Als reiner Microservice (Headless)**
Dieser Modus ist für die Integration in andere Dienste wie DreamMall gedacht. Die API ist dann im Netzwerk erreichbar.
```bash
source venv/bin/activate
python app.py
```
Die API ist unter `http://0.0.0.0:5000` verfügbar und durch den in `app.py` festgelegten API-Schlüssel geschützt.

### 3.5. Desktop-Anwendung selbst bauen

Mit dem `build_app.sh`-Skript können Sie die plattformspezifische ausführbare Datei selbst erstellen.

1.  **Stellen Sie sicher, dass alle Abhängigkeiten installiert sind:**
    ```bash
    ./setup.sh
    ```
2.  **Führen Sie das Build-Skript aus:**
    ```bash
    chmod +x build_app.sh
    ./build_app.sh
    ```
Die fertige Anwendung finden Sie anschließend im `dist/`-Ordner.
