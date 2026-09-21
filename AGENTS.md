# AGENTS.md

Repository-spezifische Arbeitsanweisung für den NLU-Service. Diese Datei beschreibt die reale
Anwendung und ist die verbindliche Quelle für Architektur, Konventionen und Qualitätsprüfungen.

## Priorität der Anweisungen

1. Explizite Anforderungen der aktuellen Aufgabe
2. Regeln in dieser Datei
3. Relevante `.agents/skills/*/SKILL.md`
4. Bestehende Projektkonventionen

Vor Änderungen relevante Skills unter `.agents/skills/` prüfen und deren `SKILL.md` lesen. Für
FastAPI-, Pydantic- und Dependency-Injection-Arbeiten ist `.agents/skills/fastapi/SKILL.md`
relevant. Unverwandte Skills nicht laden.

## Zweck und Verhalten

Der Service bietet Natural-Language-Understanding und semantisches Ranking für ein deutsches
Nachhaltigkeitsportal. Er integriert:

- Mistral für strukturierte Präferenzextraktion und kontextabhängige Rückfragen
- Nominatim/OSM für deutsches Orts-Geocoding
- SentenceTransformers und Cosine Similarity für semantisches Ranking

Öffentliche HTTP-Verträge dürfen bei Refactorings nicht still geändert werden:

| Methode | Pfad | Zweck |
|---|---|---|
| `GET` | `/health` | Liveness-Check |
| `POST` | `/api/v1/nlu/extract` | Intent- und Präferenzextraktion |
| `POST` | `/api/v1/nlu/next-question` | Nächste Dialogfrage |
| `POST` | `/api/v1/semantic/rank` | Semantisches Kandidaten-Ranking |

DTO-Feldnamen sind Teil des externen Vertrags und verwenden derzeit teilweise camelCase. Keine
automatische Umbenennung auf snake_case ohne abgestimmte API-Migration.

## Setup und Befehle

Erfordert Python 3.12+ und pip. Es gibt bewusst keine uv-/Make-Abhängigkeit.

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

Quality Gate:

```bash
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
python -m pytest -q
```

Entwicklungsserver:

```bash
fastapi dev
```

Vor Abschluss einer Änderung muss das vollständige Quality Gate grün sein. Keine Fehler mit
`# type: ignore`, `# noqa` oder gelockerten globalen Regeln verdecken. Gezielte Tool-Ausnahmen für
Bibliotheken ohne Typinformationen müssen eng begrenzt und begründet sein.

## Projektstruktur

```text
src/
├── main.py                  # create_application() und ASGI-App
├── api/
│   ├── router.py            # zentrale Router-Montage
│   ├── dependencies.py      # konkrete FastAPI-DI-Komposition
│   └── endpoints/           # ausschließlich HTTP-Schicht
│       ├── health.py
│       ├── nlu.py
│       └── semantic.py
├── core/
│   └── config.py            # Settings und einziger Env-Zugriff
├── schemas/                 # Pydantic Request-/Response-DTOs und Enums
├── nlu/                     # Mistral-, Prompt-, Geocoding- und NLU-Logik
│   └── prompts/             # verhaltensrelevante deutsche Prompts
└── semantic/                # Embedding-Modell-Lifecycle und Ranking

tests/                       # netzwerkfreie Unit- und API-Vertragstests
```

Importfluss:

```text
main → api → nlu / semantic → core
             ↘ schemas ↙
```

- `core` importiert keine API- oder Fachmodule.
- `nlu` und `semantic` importieren keine FastAPI-/HTTP-Primitiven.
- Endpoints importieren Anwendungslogik über `api.dependencies`.
- Kein Modul importiert Funktionalität aus `main.py`; nur der ASGI-Server und Tests importieren die
  App beziehungsweise `create_application()`.
- `schemas` enthält transportorientierte Pydantic-Modelle. Da der Service keine separate
  Persistenzdomäne hat, werden diese DTOs bewusst auch an den schmalen Servicegrenzen verwendet.

## FastAPI-Regeln

- Endpoints bleiben dünn: validierte Eingabe annehmen, Dependency auflösen, Service aufrufen,
  typisierte Antwort zurückgeben.
- Wiederverwendbare Dependencies als `Annotated[..., Depends(...)]` in `api/dependencies.py`.
- Dependency Overrides statt Monkeypatching verwenden, wenn API-Tests externe Clients ersetzen.
- Pro HTTP-Operation eine Handler-Funktion.
- Response-Typ oder `response_model` explizit angeben.
- Router-Prefix und Tags am jeweiligen `APIRouter` definieren.
- Die vorhandenen Mistral-, Geopy- und ML-Aufrufe sind blockierend. Zugehörige Handler bleiben
  normale `def`-Funktionen, damit FastAPI sie im Threadpool ausführt. Nicht oberflächlich auf
  `async def` wechseln; dafür müssten alle darunterliegenden I/O-Grenzen wirklich asynchron sein.
- Keine Businesslogik, Modellinitialisierung oder direkte Umgebungsabfrage in Endpoints.

## Konfiguration und Secrets

- Umgebungsvariablen ausschließlich in `core/config.py` lesen.
- Settings über `get_settings()` beziehungsweise `SettingsDep` beziehen.
- Secrets als `SecretStr` halten und nie loggen oder serialisieren.
- `MISTRAL_API_KEY` ist für Mistral-Endpunkte erforderlich, aber nicht für App-Import, Health Check,
  semantisches Ranking oder Tests.
- Neue Umgebungsvariablen zugleich typisiert in `Settings` und dokumentiert in `.env.example`
  ergänzen.
- `.env` niemals committen.

## NLU-Regeln

- `nlu/client.py` ist die einzige Mistral-SDK-Grenze.
- `nlu/extraction.py` und `nlu/questions.py` orchestrieren Anwendungsfälle.
- Promptaufbau, Präferenztext, Quick Replies, Zeitnormalisierung, Geocoding und Nachbearbeitung
  bleiben in fachlich benannten NLU-Modulen.
- Prompts sind Teil des beobachtbaren Modellverhaltens. Inhalt oder Whitespace nicht beiläufig
  durch Formatierung oder Refactoring verändern.
- Modellname, Temperaturen, JSON-Response-Format, Geocoding-Land und Matching-Schwelle nur bei
  ausdrücklicher fachlicher Änderung anpassen.
- LLM-Antworten an der Client-/Schema-Grenze validieren; ungültiges JSON nicht still akzeptieren.

## Semantic-Ranking-Regeln

- `semantic/model.py` besitzt den thread-sicheren, pro Prozess gecachten Modell-Lifecycle.
- `semantic/ranking.py` enthält Query-Aufbau, Embeddings, Chunk- und Gesamtscore.
- Das Modell wird der Ranking-Funktion explizit übergeben; kein versteckter Modellzugriff aus der
  Ranking-Logik.
- Gewichte (`0.4` Haupttext, `0.6` Chunks), `TOP_K_CHUNKS` und Score-Normalisierung sind aktuelles
  Fachverhalten und nicht ohne passende Tests ändern.
- Kein Modell-Download und keine echten Embeddings in Unit- oder API-Tests.

## Tests

- Tests müssen ohne API-Key und ohne Netzwerk laufen.
- Für HTTP-Verträge `TestClient` mit der echten App-Factory verwenden.
- Externe Services und das Embedding-Modell über `app.dependency_overrides` ersetzen.
- Reine Funktionen direkt testen, insbesondere Promptkontext, Zeitnormalisierung, Quick Replies,
  leere Ranking-Eingaben, Sortierung und Score-Grenzen.
- Bei jeder Verhaltensänderung Erfolg und relevanten Fehler-/Randfall ergänzen.
- Statuscode und Response-Body prüfen; Pfade und Methoden durch Vertragstests schützen.

## Abhängigkeiten

- Nur direkt verwendete Runtime-Pakete in `project.dependencies` führen.
- Test-, Lint- und Typwerkzeuge gehören in das `dev`-Extra.
- Keine schweren AI-, Datenbank-, Cache-, Queue- oder Auth-Abhängigkeiten ohne konkrete
  Anforderung hinzufügen.
- Standardbibliothek sowie FastAPI-/Pydantic-Funktionalität vor neuen Hilfsabstraktionen nutzen.
- Keine generischen Repository-, Manager-, Factory-, Adapter- oder Base-Service-Schichten ohne
  mehrere reale Implementierungen oder einen konkret gelösten Grenzfall einführen.

## Logging und Fehler

- `logging` verwenden; kein `print()` in Anwendungscode.
- Keine vollständigen Requests, Dialoge, Prompts, Provider-Antworten oder Secrets auf INFO loggen.
- Fehler nicht in Services als `HTTPException` ausdrücken. Falls ein stabiler fachlicher
  Fehlervertrag benötigt wird, eine kleine domänenspezifische Exception plus zentralen FastAPI-
  Handler ergänzen; nicht vorsorglich eine Hierarchie bauen.

## Deployment

- `Dockerfile` startet `src.main:app` auf Port 8000.
- Compose-Healthchecks müssen `/health` nutzen und dürfen keine im Image fehlenden Werkzeuge
  voraussetzen.
- Produktions-Secrets werden als Umgebungsvariablen injiziert und nicht ins Image kopiert.

## Arbeitsprinzipien

1. Verhalten und öffentliche Verträge zuerst sichern.
2. Löschen und vereinfachen vor neuen Abstraktionen.
3. Dateien nach fachlicher Verantwortung benennen; keine generischen Sammelmodule wie `utils.py`.
4. Änderungen klein halten und keine unabhängigen Format-/API-Änderungen beimischen.
5. Nach Moves alte Imports, Pfade, Dokumentationslinks und leere Altstrukturen suchen.
6. Das vollständige Quality Gate ausführen und nur tatsächlich ausgeführte Ergebnisse berichten.
