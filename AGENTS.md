# Dinko Petak 13

- Der Projektordner ist die Git-Grenze. Vor Git-Aktionen muss `git rev-parse --show-toplevel` auf diesen Ordner zeigen.
- Einstieg, lokaler Test und Abhängigkeiten stehen im [README](README.md). Der [Datenfluss](docs/architecture.md) beschreibt die Schnittstellen und den Stand der Anbindungen.
- Bei Änderungen an GPT-Live-Prompts oder ihrer LiveKit-Anbindung zuerst [SKILL.md](skills/gpt-live-prompting-guide/SKILL.md) und die zum Auftrag passenden Referenzen lesen.
- Änderungen an der Gesprächslogik mit dem synthetischen Testkontext prüfen. Bei Änderungen an Startparametern den LiveKit-Einstieg mit dem synthetischen Testkontext prüfen.
- Kandidatenexporte, echte Gesprächskontexte, Zugangsdaten und Gesprächsprotokolle bleiben lokal. Live-Anrufe, Airtable-Schreibzugriffe und Deployments nur im ausdrücklich beauftragten Umfang ausführen.
- Parallele Arbeiten ab einem gemeinsamen Commit auf getrennten Branches in getrennten Arbeitskopien führen. Gemeinsame Dateien vor Bearbeitung abstimmen und Änderungen vor der Zusammenführung vergleichen.
