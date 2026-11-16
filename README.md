# Dinko Petak 13

Dinko V2 ist ein Voice-Agent für Recruiting-Gespräche. Das Projekt enthält einen LiveKit-Einstieg für GPT-Live, einen Excel-Reader zur Gesprächsvorbereitung und die zugehörige Prompt-Anleitung.

## LiveKit lokal ausprobieren

Mit Python 3.10 oder neuer und einem für GPT-Live und die konfigurierte Stimme freigeschalteten OpenAI-Zugang:

```sh
uv venv .venv-livekit --python 3.10
uv pip install --python .venv-livekit/bin/python -r requirements-livekit.txt
DINKO_CONTEXT_FILE="$PWD/dinko_v2_test_context.json" DINKO_BINDINGS_FILE= .venv-livekit/bin/python dinko_v2_livekit.py console
```

Die früheren direkten OpenAI-Starter liegen als historische Fassungen in [archive/v2](archive/v2).

Für die Excel-Vorbereitung `python3 -m pip install -r requirements-excel.txt` in einer virtuellen Umgebung ausführen. Die Detailanleitung beschreibt die erwarteten Eingaben. Die LiveKit-Abhängigkeiten stehen separat in `requirements-livekit.txt`. Die Variablen in `.env.example` dienen als Vorlage für die Shell-Konfiguration.

## Kampagne Casting 18.11.2026

Ausgehender Kurzanruf mit Ergebnis in Airtable, ohne Weiterleitung. Der v2-Code bleibt unverändert.

```bash
python3 -m unittest discover -s tests          # Tests, ohne LiveKit-Pakete lauffähig
pip install -r requirements.txt
python3 dinko_kampagne_livekit.py dev          # braucht LiveKit- und OpenAI-Zugang sowie AIRTABLE_API_KEY
```

Ablauf, Airtable-Felder, Meldung und Deployment: [Kampagne](docs/kampagne.md).

- [Kampagne Casting 18.11.2026](docs/kampagne.md)
- [V2-Anleitung](Dinko%20Pet%2013%20v2%20Hinweise.md)
- [Datenfluss und Integrationsstand](docs/architecture.md)
- [Projektregeln](AGENTS.md)
- [GPT-Live-Prompting-Leitfaden](skills/gpt-live-prompting-guide/SKILL.md)
