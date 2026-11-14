# Datenfluss

1. `prepare_dinko_v2.py` liest Abfrageregeln und Casting-Angaben aus der Steuerungsmappe sowie Kandidatendaten aus einem lokalen Export. Optional ergänzt Prefetch den Kontext zum selben Kandidaten.
2. Der erzeugte Gesprächskontext enthält getrennte Angaben zum Auftrag und zum Kandidaten. `dinko_v2_prompt.py` und `dinko_v2_runtime.py` unterstützen die Aufbereitung für GPT-Live.
3. Die Python-, Node- und curl-Starter bereiten eine Session vor. `dinko_v2_livekit.py` ist der Einstieg für LiveKit. Der lokale Trockenlauf prüft die Vorbereitung der Session.
4. Externe Aktionen brauchen angebundene Handler. Die Zuordnung zum bestehenden Airtable-Ablauf und ein durchgängiger Lese- und Schreibtest bleiben eigene Arbeitsschritte.

## Casting-Aufträge

Die erste Ausgangsversion verwendet die vorhandene Excel-Steuerung. Ein Airtable-Formular mit Auftrags-ID und wiederverwendbaren Prompt-Vorlagen ist eine geplante Erweiterung. Dabei soll die Auftrags-ID gemeinsame Casting-Angaben wählen. Der Kandidatenschlüssel bleibt für personenbezogene Angaben zuständig.
