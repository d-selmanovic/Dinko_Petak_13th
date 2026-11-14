---
name: gpt-live-prompting-guide
description: Erarbeitet quellenbasierte Prompting-Leitfäden und Prompts für OpenAI GPT-Live (gpt-live-1), prüft vor dem Entwurf Unterlagen auf Lücken und erklärt Gesprächsführung, Backend-Delegation und Sprachtests. Für GPT-Live-Promptberatung und die Anpassung bestehender Voice-Prompts verwenden.
---

# GPT-Live Prompting-Leitfaden

Unterstütze den Nutzer beim Verstehen, Erstellen und Überarbeiten von Prompts für `gpt-live-1`. Prüfe vor dem Entwurf, ob seine Unterlagen für das gewünschte Ergebnis ausreichen. Passe die Prüftiefe an den Auftrag an. Für einen allgemeinen Leitfaden können Modell und Dokumentation bereits genügen.

## Vor dem Entwurf

Lies zuerst die bereitgestellten Unterlagen und den relevanten bestehenden Prompt. Übernimm belegte Angaben und bestehende Entscheidungen. Ermittle nur Informationen, die das gewünschte Ergebnis beeinflussen.

| Information | Bedeutung für den Entwurf |
| --- | --- |
| Modell und Laufzeit | `gpt-live-1`, vorhandene Session-Konfiguration und gegebenenfalls Delegationsmodus bestimmen die anwendbaren Regeln. „GPT-1“ anhand des Kontexts prüfen. Bei widersprüchlichen Modellangaben gezielt nachfragen. |
| Auftrag und Erfolg | Leitfaden, neuer Prompt, Migration oder konkrete Verhaltenskorrektur bestimmen den Umfang. |
| Agent und Gespräch | Rolle, Zielgruppe, Aufgabe, Gesprächssprache, wichtige Aussprache, Ton und tatsächliche Stimme berücksichtigen. |
| Backend | Verfügbare Fähigkeiten, Pflichtangaben, Ergebniszustände und vorhandene Verfahren prüfen, sobald der Prompt Backend-Arbeit voraussetzt. |
| Handlungsgrenzen | Bestehende Regeln zu Berechtigungen, Bestätigungen, Korrekturen, Abbruch und Übergaben übernehmen. |
| Pflichtformulierungen | Vorgeschriebene Texte und Reihenfolgen bewahren. Anforderungen an exakten Wortlaut oder Stille beeinflussen die Anwendung. |
| Beobachtungen | Für Verbesserungen verfügbare Gesprächsausschnitte, Audio, Ereignisse und Fehlfälle heranziehen. |

Melde kurz, welche Grundlage reicht, welche wesentlichen Angaben fehlen und welche Annahmen du verwendest. Frage nur nach offenen Entscheidungen, von denen der konkrete Entwurf abhängt. Setze unabhängig mögliche Arbeit fort. Formuliere einen allgemeinen Leitfaden auch dann, wenn noch kein einzelner Geschäftsfall definiert wurde. Beispielrollen und hypothetische Tools ausdrücklich als Beispiele behandeln.

Nutze für aktuelle OpenAI-Verträge die verfügbaren OpenAI-Dokumentationswerkzeuge oder offizielle Dokumentationsseiten. Prüfe relevante Modellunterschiede und widersprüchliche Quellen vor der Übernahme. Die Referenzen enthalten einen geprüften Stand und gezielte Quellenlinks.

## Passende Referenz laden

- Für Promptaufbau, Vorlage, Sprache, Stimme und optionale Verhaltensregeln lies [Prompting-Leitfaden](references/prompting-guide.md).
- Für Backend-Anbindung, Begrüßung, Kontextupdates, Stille oder Unterbrechung laufender Arbeit lies [Laufzeit und Backend](references/runtime-boundaries.md).
- Für Überarbeitung, Migration und die Bewertung eines fertigen Entwurfs lies [Prüfung und Testfälle](references/verification.md).

- Wenn der Agent das LiveKit-Plugin für GPT-Live verwendet, lies zusätzlich [LiveKit-Integration](references/livekit.md) und prüfe die installierte SDK-Version.

## Prompt entwerfen

Schreibe den gesprochenen Inhalt und die Beispiele in der gewünschten Gesprächssprache. Bewahre in GPT-Live-Prompts diese technischen Abschnittsbezeichnungen und Trigger unverändert.

- `Backchannel policy`
- `Interruption policy`
- `Delegation policy`
- `Backend tools`
- `Generate <|SpawnThinking|> when`
- `Do not generate <|SpawnThinking|> when`

Beschreibe die Gesprächsrolle, das hörbare Verhalten und konkrete Bedingungen für die Backend-Übergabe in `session.instructions` bei direkter OpenAI-Anbindung oder in `Agent.instructions` beim LiveKit-Plugin. Verwende bei `gpt-live-1` ausdrücklich `Generate <|SpawnThinking|>` für benötigte Backend-Arbeit. Eine gesprochene Ankündigung allein belegt keinen gestarteten Auftrag.

Benenne nur die belegten Backend-Fähigkeiten. Berücksichtige neue Aufträge sowie Korrekturen, Antworten auf offene Backend-Fragen und erforderliche Bestätigungen für laufende Aufgaben. Begrüßung, kurze Klärung und die Wiederholung eines noch aktuellen Ergebnisses können direkt beantwortet werden. Bei fehlenden, veralteten oder ausdrücklich erneut zu prüfenden Informationen erneut delegieren.

Die Anwendung setzt Berechtigungen und die für den jeweiligen Vorgang erforderlichen Bestätigungen durch. Bestehende Freigaben und Geschäftsregeln bestimmen diese Anforderungen. Übernimm sie in den Prompt, soweit sie beeinflussen, was der Agent sagen oder erfragen darf. Vollständige Fachverfahren, Tool-Schemata und ausführende Logik gehören in das konfigurierte Backend.

Passe die Stärke der Stilregeln an den Anwendungsfall an. Ergänze optionale Regeln bei ausdrücklichen Produktanforderungen oder belegtem Bedarf. Prüfe insbesondere Widersprüche zwischen erwünschten Hörsignalen, Sprechpausen, Unterbrechungen und Warteverhalten.

## Ergebnis liefern

Liefere den angeforderten Leitfaden oder den vollständigen Prompt in kopierbarer Form. Bei konkreten Prompts erläutere knapp wesentliche Annahmen und die dafür benötigten Backend-Fähigkeiten. Weise verbleibende Platzhalter als offenen Entwurf aus. Ein allgemeines Muster darf bewusst Anpassungsstellen enthalten.

Gib bei Änderungen an bestehenden Prompts an, welches beobachtete Problem die Änderung adressiert. Bewahre Pflichtformulierungen und weiter geltende Regeln. Benenne passende Tests mit beobachtbarem Sollverhalten.

Berichte genau, ob du den Text geprüft, ein Verhalten simuliert oder einen realen Audiolauf mit Backend und Wiedergabe geprüft hast. Für einen Leitfaden reichen Quellenprüfung und konsistente Beispiele. Aussagen über hörbare Qualität, exakte Stille, Unterbrechungslatenz und erfolgreiche Geschäftsaktionen benötigen passende Laufzeitbelege.
