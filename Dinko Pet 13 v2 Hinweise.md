# Dinko Version 2

Der LiveKit-Agent verwendet den überarbeiteten Live- und Backend-Prompt für frühere JobStep-Bewerber. Sie verwenden die bisherige Stimme, `gpt-live-1` und Responses-Delegation mit `gpt-5.6-sol`. Die Gesprächsführung setzt auf eine natürliche Vorstellung der aktuellen Gelegenheit, Interesse und freiwillige Datenklärung.

## Excel bearbeiten

Die Steuerung liegt unter [Dinko Pet 13 v2 Steuerung.xlsx](outputs/dinko-v2/Dinko%20Pet%2013%20v2%20Steuerung.xlsx).

- In **Fragen** werden Fragen aktiviert, geordnet und an Bedingungen geknüpft. `Bei fehlender Angabe` übernimmt vorhandene Werte. `Bestätigen` fordert eine gezielte Aktualisierung an.
- In **Datenfelder** werden Quellblatt und Spaltenüberschrift einem stabilen Feldnamen zugeordnet. Spalten und Fragezeilen dürfen verschoben werden. Beim Umbenennen einer Quellspalte die Zuordnung aktualisieren.
- In **Casting** stehen die Angebotsdaten und offen gebliebene Angaben. Neue Fragezeilen sind möglich. Neue Felder können aus dem Export oder dem vorhandenen Prefetch geliefert werden. Neue Bedingungstypen benötigen zusätzlich eine Anpassung des Readers.

Die Vorlage nutzt Berufserfahrung, Führerschein und Alter. Ein vorhandenes Geburtsdatum liefert das Alter am Gesprächstermin. Wenn es fehlt, fragt Dinko nur nach dem Alter. Ausbildung wird bedarfsabhängig berücksichtigt. Sprachfragen sind zunächst deaktiviert und können in Excel aktiviert werden. Die Berufserfahrungscodes bleiben bis zur Klärung ihrer Bedeutung Rohdaten. Die Ausbildungsangaben werden über die Kandidaten-ID verknüpft. Das Blatt `Archiv` ist keine automatische Anrufliste.

Quelle der Feldzuordnung ist die bereitgestellte Datei `Kandidaten_Struke_Tiefbau.xlsx`. Die Angaben zum Angebot stammen aus Version 1 und den im Gespräch bestätigten Angaben. Die Anreise bezahlt der Kandidat. Ein zusätzliches Dokumentenverfahren ist bisher nicht festgelegt.

## Lokalen Kontext vorbereiten

Voraussetzung für den Excel-Reader ist Python ab 3.10 mit `openpyxl`. Auf diesem Rechner steht das Paket bereits im gebündelten Python bereit. Für eine andere Umgebung wird die Abhängigkeit mit `python3 -m pip install openpyxl` installiert.

Den Befehl im Projektordner ausführen und die Kandidaten-ID gezielt einsetzen. Der Ausgabepfad muss neu sein, damit kein anderer Gesprächskontext überschrieben wird.

```bash
python3 prepare_dinko_v2.py \
  --rules 'outputs/dinko-v2/Dinko Pet 13 v2 Steuerung.xlsx' \
  --candidates '/Users/activi/Downloads/Kandidaten_Struke_Tiefbau.xlsx' \
  --candidate-id "$DINKO_CANDIDATE_ID" \
  --output dinko-context.json
```

Auf diesem Rechner kann der Python-Aufruf durch `/Users/activi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3` ersetzt werden.

Der Reader arbeitet mit Spaltennamen, Kandidaten-ID und Feld-ID. Fehlende optionale Spalten erzeugen einen Hinweis und eine offene Angabe. Doppelte Kandidaten-IDs, doppelte Regelkennungen und ungültige Regeln führen zu einer verständlichen Fehlermeldung. Leere Werte, `false`, null Monate und eine nicht anwendbare Frage bleiben unterscheidbar.

Ein vorhandener Vorab-Code kann per `--prefetch` ein JSON-Objekt mit `candidate_id` und `fields` übergeben. `fields` verwendet die Feld-IDs aus Excel und enthält bereits normalisierte, tatsächlich bekannte Angaben. Dieser aktuelle Kontext hat Vorrang vor dem Export. Hier können insbesondere `experience_tasks` und `experience_duration` geliefert werden. Die ID muss zum ausgewählten Kandidaten passen. Freitextantworten und neue Angaben werden während des Gesprächs weiter ergänzt.

## Start über LiveKit

Der aktive Einstieg ist `dinko_v2_livekit.py`. Der lokale Test steht weiter unten. Die direkten OpenAI-Starter liegen als historische Fassungen unter `archive/v2/`.

## Airtable und echte Aktionen anbinden

Für den ersten V2-Anschluss ist die vorhandene Airtable-Anbindung die Arbeitsannahme, weil laut Nutzer bereits ein Ablauf zum Lesen und Schreiben besteht. Vor einem neuen Datenbestand sollte dessen konkrete Tabellen- und Feldzuordnung geprüft werden. Die hier erstellten Dateien migrieren keine Datensätze.

Die Anwendung liest vor dem Gespräch den aktuellen Datensatz über die Kandidaten-ID, ergänzt die Excel-Regeln und übergibt den Kontext. Für Rückschreiben verwendet sie den tatsächlich zugehörigen Airtable-Record-ID und die bekannten Feld-IDs. Bei einer MySQL-Anbindung bleibt der fachliche Gesprächskontext gleich. Nur der vorhandene Datenadapter übernimmt Lesen und Schreiben.

`DINKO_BINDINGS_FILE` kann ein JSON mit `tools` und `capabilities` laden. `tools` enthält die echten OpenAI-Funktionsdefinitionen oder MCP-Verbindungen. Jede Fähigkeit in `capabilities` benennt `purpose`, `description` und entweder einen exakt passenden `tool_name` oder `server_label`. Zugangsdaten gehören ausschließlich in die geschützte Laufzeitkonfiguration.

Der Betreiber muss für jede Funktion den ausführenden Handler bereitstellen. Eine Tool-Beschreibung allein führt keinen Airtable-Zugriff aus. Ohne Bindings sind keine externen Tools aktiv. Der Agent kann den Gesprächskontext nutzen und Antworten aufnehmen, bestätigt aber keine dauerhafte Speicherung oder Terminbuchung.

Die Anwendung speichert nur neue oder korrigierte Felder, erhält andere Angaben und ordnet Änderungen dem richtigen Kandidaten zu. Pro Gespräch und Schreibvorgang werden eindeutige Kennungen und der Ausführungsstatus benötigt. Ungewisse Ergebnisse vor erneutem Schreiben abgleichen. Gegenläufige Änderungen und Abbruchwünsche berücksichtigen. Ob ein bestehender Ablauf direkt im Kandidatendatensatz oder in einer Ergänzungstabelle speichert, muss an dessen aktuellem Vertrag geprüft werden.

Die Freigabe der Eignung erfolgt durch das Team. Ein daran angebundener Terminablauf kann danach automatisch durchgeführt werden. `team_review.invitation_approved` darf die Anwendung nur aus einer bestätigten Entscheidung für genau diese Person und Kampagne setzen. Freie Plätze, Adresse und erfolgreiche Buchung müssen aus dem angebundenen System stammen.

## Noch benötigte Angaben für den Betrieb

- Konkrete Airtable-Base, Tabellen und Feldzuordnung sowie der bisherige Prefetch- und Schreibablauf.
- Die Codelegende der Berufserfahrung und die tatsächlich geforderten Führerscheinklassen.
- Konkrete Vorgaben für ausreichende Erfahrung bzw. die ergänzende Ausbildung. Die Vorlage erfindet keinen Erfahrungsgrenzwert.
- Einladungsgenehmigung durch das Team, genaue Castingadresse und verfügbare Buchungszeiten.

Die Dateien wurden lokal vorbereitet. Modell- und Stimmzugriff, Telefonie, dauerhafte Datenspeicherung, Terminbuchung und hörbare Gesprächsqualität brauchen einen verbundenen Laufzeittest.

## LiveKit-Plugin testen

Mit einem autorisierten OpenAI-Schlüssel für GPT-Live und die konfigurierte Custom Voice:

```bash
uv venv .venv-livekit --python 3.10
uv pip install --python .venv-livekit/bin/python -r requirements-livekit.txt
DINKO_CONTEXT_FILE="$PWD/dinko_v2_test_context.json" DINKO_BINDINGS_FILE= .venv-livekit/bin/python dinko_v2_livekit.py console
```

Der lokale Konsolenmodus benötigt keinen LiveKit-Raum. Warte zunächst auf die bosnische Begrüßung und gleiche die Stimme mit einer Referenzaufnahme ab. Bestätige die synthetische Identität Amir. Unterbrich eine längere Antwort mit „stani“ und prüfe die hörbare Restsprechdauer. Frage nach dem Castingdatum und bestätige anhand des Laufzeitprotokolls, dass die Antwort nach einer Responses-Delegation den synthetischen Termin wiedergibt. Die Fixture enthält keine echten Kandidatendaten. Direkte OpenAI-Tool-Bindings brauchen ausführbare LiveKit-Adapter.
