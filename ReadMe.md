# NLU Service

Dieser Microservice erweitert die Plattform um Funktionen zur Verarbeitung natürlicher Sprache und zur semantischen Sortierung von Suchergebnissen.

Der Service basiert auf **FastAPI** und stellt unter anderem Endpunkte für folgende Funktionen bereit:

* Extraktion von Intentionen und Benutzerpräferenzen
* Generierung kontextabhängiger Rückfragen
* Semantisches Ranking von Suchergebnissen
* Überprüfung des Service-Status

## Voraussetzungen

Für die Ausführung werden folgende Komponenten benötigt:

* Python 3.11 oder neuer
* `pip`
* Zugriff auf das konfigurierte Mistral-Sprachmodell

## Installation

Zunächst sollte eine virtuelle Python-Umgebung erstellt werden.

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### Linux und macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Anschließend können die benötigten Abhängigkeiten installiert werden:

```bash
python -m pip install -e .
```

## Umgebungsvariablen

Für die Ausführung wird eine `.env`-Datei benötigt.

Die verwendete `.env`-Datei befindet sich auf dem zusammen mit der Bachelorarbeit abgegebenen USB-Datenträger. Sie ist nicht Bestandteil des öffentlichen Repositorys, da sie sensible Konfigurationswerte und Zugangsdaten enthalten kann.

Die Datei muss im Stammverzeichnis des Projekts abgelegt werden:

```text
nlu-service/
├── .env
├── requirements.txt
└── src/
    └── main.py
```

Die `.env`-Datei darf nicht in das öffentliche Repository eingecheckt werden. Sie sollte daher in der `.gitignore` enthalten sein:

```gitignore
.env
```

## Anwendung starten

Der Microservice kann aus dem Stammverzeichnis des Projekts mit folgendem Befehl gestartet werden:

```powershell
fastapi dev .\src\main.py
```

Unter Linux oder macOS kann alternativ folgender Pfad verwendet werden:

```bash
fastapi dev ./src/main.py
```

Standardmäßig ist die Anwendung anschließend unter folgender Adresse erreichbar:

```text
http://127.0.0.1:8000
```

## API-Dokumentation

FastAPI stellt automatisch eine interaktive API-Dokumentation bereit.

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

## API-Endpunkte

### Health Check

```http
GET /health
```

Überprüft, ob der Microservice erreichbar und funktionsfähig ist.

### NLU-Extraktion

```http
POST /api/v1/nlu/extract
```

Analysiert eine Benutzernachricht und extrahiert unter anderem die erkannte Intention, den Nachrichtentyp und vorhandene Suchpräferenzen.

### Generierung der nächsten Frage

```http
POST /api/v1/nlu/next-question
```

Generiert abhängig vom bisherigen Dialog, den bekannten Präferenzen und dem noch fehlenden Feld eine passende Rückfrage.

### Semantisches Ranking

```http
POST /api/v1/semantic/rank
```

Sortiert übergebene Kandidaten anhand ihrer semantischen Ähnlichkeit zu den Suchpräferenzen des Benutzers.

## Projektstruktur

```text
src/
├── api/
│   ├── routes_nlu.py
│   └── routes_semantic.py
├── schemas/
│   ├── health.py
│   ├── nlu.py
│   └── semantic.py
├── services/
│   ├── extraction_service.py
│   ├── question_service.py
│   └── semantic_ranker.py
└── main.py
```

* `api`: Definition der REST-Endpunkte
* `schemas`: Pydantic-Modelle für Anfragen und Antworten
* `services`: Fachliche Verarbeitung der Anfragen
* `main.py`: Initialisierung und Konfiguration der FastAPI-Anwendung

## Logging

Der Microservice verwendet das Python-Modul `logging`. Die Log-Ausgaben enthalten Informationen über eingehende Anfragen, erzeugte Antworten sowie die Dauer des semantischen Rankings.

Die Logging-Konfiguration befindet sich in `src/main.py`.

## Hinweise

Der Microservice ist als Bestandteil einer prototypischen Systemerweiterung im Rahmen einer Bachelorarbeit entstanden. Der Quellcode dient der Dokumentation und Reproduzierbarkeit der implementierten Funktionen.

### Einsatz von Künstlicher Intelligenz

Bei der Erstellung und Überarbeitung einzelner Inhalte dieses Repositorys wurde Künstliche Intelligenz unterstützend eingesetzt. Dies betrifft insbesondere die Formulierung und sprachliche Überarbeitung von Dokumentationen, Kommentaren und beschreibenden Texten.

Die fachliche Prüfung, Anpassung und abschließende Verantwortung für sämtliche Inhalte lagen beim Autor des Projekts.