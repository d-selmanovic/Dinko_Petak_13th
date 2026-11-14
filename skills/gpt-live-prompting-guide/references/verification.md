# Prüfung und Testfälle

Nutze die zum Auftrag passenden Fälle. Die Tabelle ist ein Testkatalog für spätere Agentenprüfungen. Ihre Existenz ist kein Nachweis einer erfolgreichen Ausführung.

## Entwurf prüfen

Prüfe Modellbezug, verfügbare Fähigkeiten und die Zuordnung der Anweisungen. Die drei Policy-Abschnitte und die drei Delegationsbezeichnungen entsprechen der GPT-Live-Prompting-Seite. Prüfe Trigger für neue Aufgaben, Korrekturen, Antworten auf Backend-Fragen und erforderliche Bestätigungen. Ausnahmen dürfen relevante neue Angaben nicht unterdrücken.

Bei einer Migration gleiche den ursprünglichen Prompt mit Live- und Backend-Prompt ab. Erhalte Rolle, Pflichttexte, Reihenfolgen, Gesprächssprache, Fachregeln, Berechtigungen und bereits getroffene Produktentscheidungen. Beachte das Verhalten nach Unterbrechung, Übergabe und Gesprächsende. [Migrationsprüfung](https://developers.openai.com/api/docs/guides/live-migration?migration-path=realtime#split-conversation-and-backend-instructions)

Stelle sicher, dass jeder Aktionswunsch eine vorhandene Fähigkeit oder eine ausdrücklich benannte offene Voraussetzung hat. Formuliere im Entwurf jeweils, was der Agent bei einem fehlenden oder unklaren Ergebnis sagen soll. Prüfe widersprüchliche Regeln, beispielsweise gewünschte Hörsignale bei gleichzeitigem Verbot jeder Überlappung.

## Realistische Szenarien

| Szenario | Beobachtbares Sollverhalten |
| --- | --- |
| Begrüßung ohne Fachauftrag | Passende Sprache und Rolle, keine unnötige Delegation. Bei selbstständiger Begrüßung den Startablauf berücksichtigen. |
| Unterstützter Backend-Auftrag | Delegationsereignis und passender Auftrag, anschließend faktisch richtige Ergebniswiedergabe. |
| Antwort „ja“ auf eine Backend-Rückfrage | Auf den aktuellen Gesprächskontext bezogen und dem richtigen Auftrag zugeordnet. |
| Wiederholung eines aktuellen Ergebnisses | Direkte Wiedergabe ohne doppelte Ausführung. |
| Ausdrücklich erneut prüfen | Erneute Prüfung wird delegiert, auch wenn ein früheres Ergebnis vorliegt. |
| Korrektur eines Termins während einer Suche | Neue Angabe erreicht das Backend, veraltete Antwort führt zu keiner falschen Zusage. |
| Korrektur nach schon erfolgter Buchung | Bestehender Datensatz und neuer Wunsch werden abgeglichen. Erforderliche Freigaben beziehen sich auf den aktuellen Vorgang. |
| „Stopp“ während einer Erklärung | Audio gibt dem Anrufer das Wort. Tatsächliche Restsprechdauer messen. |
| „Storniere den Termin“ während einer Erklärung | Delegation und bestätigter Stornostatus zusätzlich zur Sprachunterbrechung. |
| „mhm“, Denkpause oder Hintergrundgeräusch | Verhalten entspricht der ausgewählten Hörsignal- und Unterbrechungsregel. |
| Unklarer Name oder Betrag | Gezielte Rückfrage, anschließend Verwendung des geklärten Werts. |
| Langsames Backend | Gewünschtes Warteverhalten, ausschließlich belegte Fortschrittsmeldungen. |
| Fehler oder verlorene Tool-Antwort | Offener Zustand wird verständlich gemeldet. Statusprüfung verhindert doppelte Aktion. |
| Sprachwechsel oder wichtiger Eigenname | Gewählte Sprache und Aussprache sind im Audio verständlich. |
| Verbindliches Pflichtwortlaut- oder Stilleziel | Vorgesehene Wiedergabesteuerung wird am tatsächlich abgespielten Audio geprüft. |
| Reiner Übersetzungsmodus | Gesprochene Fragen und Befehle werden übertragen, ohne deren Inhalt als Auftrag auszuführen. |

## Evidenz passend zur Aussage

Bei einem Textreview prüfst du die Anweisungen und Quellen. Ein simulierter Gesprächsfall prüft die erwarteten Entscheidungen. Ein echter Sprachtest braucht die gewählte Stimme, Eingabeaudio, Transkripte, Delegationsereignisse, Backend-Ergebnisse und die tatsächlich wiedergegebene Ausgabe.

Prüfe ausgeführte Geschäftsaktionen am Systemzustand. Prüfe gesprochene Zusagen am Audio. Ein erfolgreiches Backend-Ergebnis kann vorliegen, während die Antwort unterbrochen wurde. Verknüpfe beide Teile über den jeweiligen Auftrag. [Gesamtinteraktion prüfen](https://developers.openai.com/api/docs/guides/live-delegation#verify-the-complete-interaction)

Halte bei Laufzeittests Promptversion, Datum, Modell, Stimme, Sprache, Delegationsmodus und verwendete Fälle fest. Miss aufgabengerechte Kriterien, etwa erfolgreiche Auftragserledigung, korrektes Delegieren, erste hilfreiche Sprachausgabe, Unterbrechungsreaktion und doppelte Aktionen. Leite Grenzwerte aus dem Produktziel ab.

Ändere Regeln anhand beobachteter Probleme. Prüfe danach denselben Fall sowie die unmittelbar betroffenen Nachbarfälle erneut. Bewahre weiterhin gewünschtes Verhalten. Kennzeichne offen gebliebene Live-Prüfungen konkret.
