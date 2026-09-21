# NLU Service

FastAPI-Microservice für ein deutsches Nachhaltigkeitsportal. Er bietet:

* strukturierte Intent- und Präferenzextraktion über Mistral,
* kontextabhängige Rückfragen,
* deutsches Orts-Geocoding über Nominatim/OSM,
* semantisches Ranking über SentenceTransformers.

## Voraussetzungen

* Python 3.12 oder neuer
* `pip`
* `MISTRAL_API_KEY` für die beiden NLU-Endpunkte
* Netzwerkzugriff für Mistral, Nominatim und den initialen Download des Embedding-Modells

Health Check, App-Import und Tests benötigen weder API-Key noch Netzwerk.

## Installation

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

### Linux und macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
```

Anschließend `MISTRAL_API_KEY` in der lokalen `.env` setzen. `.env` ist git-ignoriert und darf
nicht committed werden.

## Anwendung starten

Der FastAPI-Einstiegspunkt ist in `pyproject.toml` konfiguriert:

```powershell
fastapi dev
```

Alternativ:

```powershell
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Swagger UI: <http://127.0.0.1:8000/docs>

ReDoc: <http://127.0.0.1:8000/redoc>

## API

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/health` | Liveness-Check |
| `POST` | `/api/v1/nlu/extract` | Intent und Präferenzen extrahieren |
| `POST` | `/api/v1/nlu/next-question` | Nächste Dialogfrage erzeugen |
| `POST` | `/api/v1/semantic/rank` | Kandidaten semantisch sortieren |

Die bestehenden DTOs und camelCase-Feldnamen sind Teil des externen API-Vertrags.

## Architektur

```text
src/
├── main.py
├── api/
│   ├── router.py
│   ├── dependencies.py
│   └── endpoints/
│       ├── health.py
│       ├── nlu.py
│       └── semantic.py
├── core/
│   └── config.py
├── schemas/
├── nlu/
│   ├── client.py
│   ├── extraction.py
│   ├── questions.py
│   ├── messages.py
│   ├── preferences.py
│   ├── postprocessing.py
│   ├── geocoding.py
│   ├── timezones.py
│   ├── quick_replies.py
│   └── prompts/
└── semantic/
    ├── model.py
    └── ranking.py

tests/
```

* `api/endpoints`: dünne HTTP-Schicht
* `api/dependencies.py`: FastAPI-Komposition und austauschbare externe Abhängigkeiten
* `core/config.py`: zentrale Settings und einziger Zugriff auf Umgebungsvariablen
* `schemas`: Pydantic Request-/Response-Verträge und Enums
* `nlu`: Mistral-, Prompt-, Geocoding- und Dialoglogik
* `semantic`: Modell-Lifecycle und Ranking-Algorithmus

Die blockierenden Mistral-, Geopy- und ML-Aufrufe werden bewusst über synchrone FastAPI-Handler
aufgerufen; FastAPI führt diese im Threadpool aus.

## Qualität prüfen

```powershell
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
python -m pytest -q
```

Die Tests ersetzen Mistral und das Embedding-Modell über FastAPI Dependency Overrides. Sie führen
keine Netzwerkaufrufe und keinen Modelldownload aus.

## Container

Image bauen und starten:

```powershell
docker compose build
docker compose up
```

Für NLU-Aufrufe muss `MISTRAL_API_KEY` in der Umgebung beziehungsweise lokalen `.env` gesetzt sein.
Der Container stellt Port 8000 bereit und prüft `/health`.
