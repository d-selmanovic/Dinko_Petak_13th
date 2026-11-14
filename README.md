# Dinko Petak 13

Dinko V2 ist ein Voice-Agent für Recruiting-Gespräche. Das Projekt enthält Starter für GPT-Live, einen LiveKit-Einstieg, einen Excel-Reader zur Gesprächsvorbereitung und die zugehörige Prompt-Anleitung.

## Lokal ausprobieren

Mit Python 3.10 oder neuer lässt sich die Vorbereitung der Session mit synthetischen Daten prüfen.

```sh
export DINKO_CONTEXT_FILE="$PWD/dinko_v2_test_context.json"
DINKO_DRY_RUN=1 python3 'Dinko Pet 13 v2 python.py'
DINKO_DRY_RUN=1 node 'Dinko Pet 13 v2 node.mjs'
DINKO_DRY_RUN=1 bash 'Dinko Pet 13 v2 curl.sh'
```

Der Node-Starter braucht Node.js mit `fetch` und `AbortSignal.timeout`. Für den curl-Starter werden `curl` und `jq` benötigt. Der Trockenlauf verwendet keinen OpenAI-Schlüssel.

Für die Excel-Vorbereitung `python3 -m pip install -r requirements-excel.txt` in einer virtuellen Umgebung ausführen. Die Detailanleitung beschreibt die erwarteten Eingaben. Die LiveKit-Abhängigkeiten stehen separat in `requirements-livekit.txt`. Die Variablen in `.env.example` dienen als Vorlage für die Shell-Konfiguration.

- [V2-Anleitung](Dinko%20Pet%2013%20v2%20Hinweise.md)
- [Datenfluss und Integrationsstand](docs/architecture.md)
- [Projektregeln](AGENTS.md)
- [GPT-Live-Prompting-Leitfaden](skills/gpt-live-prompting-guide/SKILL.md)
