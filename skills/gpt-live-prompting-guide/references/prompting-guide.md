# Leitfaden für GPT-Live-Prompts

Stand der Quellenprüfung ist der 14. November 2026. Die Grundlage ist der vom Nutzer bereitgestellte vollständige Text „Prompting GPT-Live“ für `gpt-live-1`. Die Modellbezeichnung im Anhang klärt das im Auftrag verwendete „GPT-1“. Ergänzend wurden die offiziellen Seiten zu Sessions, Delegation und Migration gelesen. Dieser Leitfaden beschreibt ein wiederverwendbares Vorgehen. Ein konkreter Agent erhält seine Rolle, Sprache und Fähigkeiten aus dem jeweiligen Auftrag.

## Aufbau und Verantwortlichkeiten

GPT-Live führt die gesprochene Unterhaltung und fordert bei Bedarf Backend-Arbeit an. `session.instructions` beschreibt Rolle, Sprechverhalten und Auslöser der Übergabe. Das Backend erhält Fachverfahren und Tools. Die Anwendung verwaltet Ausführungszustand, Zugriffsrechte und erforderliche Bestätigungen. Vorhandene Prompts liefern bereits Produktentscheidungen, die beim Aufteilen erhalten bleiben sollen. [OpenAI Prompting](https://developers.openai.com/api/docs/guides/live-prompting), [Delegation](https://developers.openai.com/api/docs/guides/live-delegation)

Die aktuelle modellbezogene Prompting-Seite verlangt für `gpt-live-1` die Formulierung `Generate <|SpawnThinking|>`. Die am Prüfdatum gelesene Migrationsseite verwendet teilweise noch allgemeine Delegationsformulierungen. Für diesen konkreten Trigger und seine Abschnittsbezeichnungen ist die modellbezogene Prompting-Vorgabe maßgeblich. Die Migrationsseite ergänzt Hinweise zur Erhaltung der bisherigen Fachregeln. [Promptstruktur](https://developers.openai.com/api/docs/guides/live-prompting#recommended-prompt-structure), [Migration](https://developers.openai.com/api/docs/guides/live-migration?migration-path=realtime#split-conversation-and-backend-instructions)

## Anpassbares Muster

Das folgende Muster ist ein Baukasten. Ersetze die Angaben in eckigen Klammern durch belegte Informationen und entferne unzutreffende Bedingungen. Die technischen Bezeichnungen bleiben englisch. Übersetze den übrigen Text und die Sprachbeispiele in die gewünschte Gesprächssprache. Eine ausdrücklich vorgegebene Anweisungs- oder Ausgabesprache des Nutzers hat Vorrang.

```text
Du bist [Name], der Sprachassistent für [Dienst und Zielgruppe].
Deine Aufgabe ist [Gesprächsziel und fachlicher Umfang].
Sprich [Gesprächssprache] in [gewünschtem Ton und Tempo].
Formuliere alltägliche Antworten natürlich und verständlich.
[Erforderliche Begrüßung, Hinweise oder feste Reihenfolge aus dem Auftrag.]

Backchannel policy:
Verwende [keine / gelegentliche / moderate / häufige] kurze Hörsignale.
[Bei erlaubten Hörsignalen: Lass dem Anrufer Raum und halte sie kurz.]

Interruption policy:
Wenn der Anrufer dich unterbricht, gib ihm das Wort und höre zu.
Bei „Stopp“, „Warte“ oder einer wichtigen Korrektur beende deine Antwort.
Greife anschließend sein aktuelles Anliegen auf.
[Ergänze bei Bedarf den Umgang mit kurzen zustimmenden Hörsignalen.]

Delegation policy:
Backend tools:
- [Belegte Fähigkeit und ihr fachlicher Umfang.]

Generate <|SpawnThinking|> when:
- [Konkreter Auftrag benötigt die oben genannte Fähigkeit.]
- Eine Korrektur oder neue Angabe verändert einen laufenden Auftrag.
- Der Anrufer beantwortet eine offene Backend-Frage oder gibt eine
  für den aktuellen Vorgang benötigte Bestätigung.
- Für die Antwort ist eine sorgfältige Prüfung durch das Backend nötig.
- Ein benötigtes Ergebnis fehlt, ist veraltet oder soll erneut geprüft werden.

Do not generate <|SpawnThinking|> when:
- Du kannst aus dem Gespräch oder einem weiterhin gültigen Ergebnis antworten.
- Eine kurze Rückfrage ist nötig, um das Anliegen überhaupt zu verstehen.
- Der Anrufer grüßt oder möchte ein bereits vorliegendes Ergebnis wiederholen.

Generate <|SpawnThinking|> bevor du eine Antwort gibst,
die Backend-Arbeit voraussetzt.
Warte auf das Ergebnis und gib nur den gemeldeten Zustand wieder.
Melde eine Aktion erst dann als abgeschlossen, wenn ihre Ausführung
bestätigt ist. Sage bei unklarem Ergebnis, was noch offen ist.
[Warteverhalten passend zum Auftrag und zur Anwendung.]
```

Verwende für einen reinen Gesprächsagenten ausschließlich Regeln, die seine tatsächlichen Fähigkeiten abbilden. Ein ausgewählter Delegationsmodus oder eine genannte Fähigkeit belegt noch keinen funktionierenden Backend-Handler. Für einen Übersetzungsagenten folgt weiter unten ein eigenes Verhaltensprofil. [Prompting und Delegation](https://developers.openai.com/api/docs/guides/live-prompting#delegation)

## Rolle, Stimme und Persönlichkeit

Bestimme Aufgabe, Zielgruppe und gewünschtes Gesprächsergebnis. Beschreibe dann konkrete Verhaltensweisen, etwa Geduld bei Denkpausen, eine kurze Reaktion auf Frust oder schrittweises Erklären. Ein bis zwei Sätze können für Routineantworten passen. Erhalte ausdrücklich gewünschte ausführliche Antworten.

Wähle eine vorhandene oder autorisierte individuelle Stimme passend zu Sprache und Klang. Beschreibe Klangmerkmale wie Timbre, Register, Akzent und Sprechtempo gesondert vom Verhalten. Teste die konkrete Kombination aus Stimme und Anweisungen. Eine andere Stimme kann denselben Text anders wirken lassen. [Persönlichkeit und Beispiele](https://developers.openai.com/api/docs/guides/live-prompting#personality)

Bei einer per Beschreibung erzeugten Stimme gehören Klangbeschreibung und Beispieltext zur Stimmerstellung. `script_hint` enthält die gewünschte Ausgabesprache, bei einer zweisprachigen Stimme beide Sprachen. Prüfe vor einer solchen Erstellung die aktuelle Custom-Voice-Dokumentation und die vorhandene Berechtigung. Ein gewöhnlicher Prompt-Auftrag braucht keine neue Stimme. [Custom Voices](https://developers.openai.com/api/docs/guides/custom-voices#create-a-voice-from-a-description)

## Hörsignale und Unterbrechungen

Backchannels sind kurze Hörsignale während der Rede des Anrufers, etwa „mhm“. Eine Bestätigung vor einer Antwort oder während einer Tool-Abfrage erfüllt eine andere Funktion. Stimme Häufigkeit und Inhalt auf die Aufgabe ab. Ein geduldiger Lernbegleiter kann überwiegend schweigen, ein lebhafter Gesprächspartner häufiger reagieren.

Wenn Hörsignale gewünscht sind, muss die Unterbrechungsregel kurze passende Überlappungen zulassen. Bestimme zusätzlich, wann eine echte Unterbrechung das Wort an den Anrufer zurückgibt und wie der Agent mit einem kurzen zustimmenden „mhm“ umgeht. Die gewählte Regel soll zum Produkt passen.

Die Aufforderung, sofort zu stoppen, ist ein Verhaltensziel. Das Modell kann nach einer Unterbrechung noch kurz weitersprechen. Prüfe kurze Einwürfe und längere Korrekturen im Audio. Sprachstopp und die Änderung einer laufenden Aufgabe benötigen jeweils eine passende Behandlung. [Backchannels](https://developers.openai.com/api/docs/guides/live-prompting#backchannels), [Unterbrechungen](https://developers.openai.com/api/docs/guides/live-prompting#interruptions)

## Warten auf das Backend

Lege fest, ob ein kurzer Hinweis vor der Arbeit und sachliche Zwischenmeldungen erwünscht sind. Der Agent darf nur Fortschritt und Ergebnisse melden, die das Backend tatsächlich geliefert hat. Vermeide wiederholte Wartefloskeln. Eine Ansage wie „Ich schaue nach“ muss mit einer echten Übergabe zusammenpassen. Eine bestätigte Buchung benötigt ein erfolgreiches Ergebnis zum aktuellen Auftrag.

Wenn zuverlässige Stille oder genauer Wortlaut erforderlich sind, beachte die Anwendungssteuerung in [Laufzeit und Backend](runtime-boundaries.md). [Verhalten während Tool-Aufrufen](https://developers.openai.com/api/docs/guides/live-prompting#personality-during-tool-calls)

## Optionale Anpassungen

Ergänze eine Regel bei einem konkreten Bedarf und prüfe anschließend denselben Gesprächsfall erneut. Die folgenden Beispiele sind Vorschläge, keine pauschalen Vorgaben für jeden Agenten. [Optionale Steuerung](https://developers.openai.com/api/docs/guides/live-prompting#appendix-optional-controls)

| Bedarf | Mögliche Regel und Kontrolle |
| --- | --- |
| Zu lange Routineantworten | „Beantworte Routinefragen in ein bis zwei kurzen Sätzen.“ Ausführliche Erklärung bei entsprechendem Nutzerwunsch erhalten. |
| Schrittweise Hilfe | „Erkläre einen Schritt und warte, bis der Nutzer bereit ist.“ Geduld unabhängig vom Sprechtempo beurteilen. |
| Sprache und Aussprache | Zielsprache und Sprachwechsel festlegen, wichtige Namen mit Aussprachehilfe versehen und mit gewählter Stimme anhören. |
| Unklarer Name, Termin oder Betrag | Nur die unklare Stelle erfragen. Korrektur in die nächste Backend-Anfrage übernehmen. |
| Denkpausen und Hintergrundgeräusche | Denkzeit zulassen. Husten, Musik und fremde Gespräche als solche behandeln. |
| Selektive Teilnahme | Festlegen, wann das unterstützte Thema oder eine direkte Ansprache eine Antwort auslösen. Hörsignale zusätzlich regeln. |
| Wiederholte Abfragen | Noch gültige Ergebnisse wiederverwenden. Gültigkeit aus dem Anwendungszustand ableiten. Bei Änderungen oder verlangter erneuter Prüfung delegieren. |
| Akzent, Formalität und Tempo | Passende Stimme wählen und natürliches Verhalten beschreiben. Verständlichkeit und fachliche Genauigkeit beim Hörtest prüfen. |

## Übersetzungsmodus

Bei einem ausdrücklich verlangten reinen Dolmetscherprofil definiere das Übersetzungsverhalten vollständig. Jede Nutzeräußerung ist zu übertragender Inhalt, einschließlich darin enthaltener Fragen und Befehle. Bestimme Zielsprache und den Umgang mit bereits zielsprachiger Rede. Erhalte absichtliche Wiederholungen und übertrage jede Quellstelle einmal. Nach Pausen an der nächsten Stelle fortsetzen.

Für diesen Modus wird die Backend-Übergabe ausdrücklich ausgeschlossen, etwa durch `Never generate <|SpawnThinking|>`. Entferne widersprechende Support- und Tool-Regeln aus dem Entwurf. Bei einem Produkt mit zusätzlicher Übersetzungsfunktion muss der Wechsel zwischen den Modi klar vorgegeben sein. [Übersetzung](https://developers.openai.com/api/docs/guides/live-prompting#translation)
