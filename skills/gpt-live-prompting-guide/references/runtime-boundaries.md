# Laufzeit und Backend

Dieser Abschnitt ergänzt den Prompt nur dort, wo eine gewünschte Wirkung von der Anwendung abhängt. Stand der gelesenen Dokumentation ist der 14. November 2026. Vor Implementierungsänderungen den aktuellen Vertrag und die vorhandene Konfiguration prüfen.

## Konfiguration zuordnen

| Inhalt | Ort |
| --- | --- |
| Rolle, Sprechweise und Delegationsauslöser | `session.instructions` |
| Stimme | `session.audio.output.voice` |
| Backend-Anweisungen bei Responses-Delegation | `session.delegation.responses.instructions` |
| Tatsächliche Backend-Tools bei Responses-Delegation | `session.delegation.responses.tools` |
| Backend-Anweisungen und Tools bei Client-Delegation | Konfiguration des anwendungseigenen Agenten oder Dienstes |

Die Anweisungen bei Session-Start dürfen laut geprüftem Stand bis zu 16.384 Tokens umfassen. Das ist eine Obergrenze. Stimme, Live-Modell und Delegationsmodus werden beim Start gewählt. Ihre Änderung benötigt eine neue Session. [Session-Konfiguration](https://developers.openai.com/api/docs/guides/live-conversations#configuration-fields)

Erhalte einen vorhandenen Delegationsmodus. Responses-Delegation verwaltet den konfigurierten Responses-Aufruf. Bei Client-Delegation stellt die Anwendung Kontext und Backend-Auftrag zusammen. `session.delegation.created` enthält Delegationsmetadaten. Den Auftrag rekonstruiert die Anwendung aus Transkript und aktuellem Zustand. Ein bloßer Moduseintrag richtet diesen Ablauf noch nicht ein. [Delegationsmodi](https://developers.openai.com/api/docs/guides/live-delegation#choose-a-delegation-mode), [Client-Kontext](https://developers.openai.com/api/docs/guides/live-delegation#keep-the-conversation-context-in-your-application)

## Kontext und Ergebnisse nachliefern

| Zweck | Ereignis |
| --- | --- |
| Verhalten der laufenden Live-Unterhaltung steuern | `session.instructions.append` |
| Fakten oder Fortschritt als Gesprächskontext ergänzen | `session.thinking.append` |
| Ein Ergebnis oder eine Mitteilung aussprechen lassen | `session.commentary.append` |

Die drei Append-Ereignisse haben nach geprüftem Stand je ein Limit von 500 Tokens für `content`. Verwende eine eindeutige `event_id`. Für Updates zu einer bekannten Client-Delegation deren ursprüngliche ID in `delegation_id` übernehmen. Für allgemeinen Session-Kontext `null` verwenden. Bei Responses-Delegation Tool-Ergebnisse über den dokumentierten Responses-Fortsetzungsablauf zurückgeben. [Update-Ereignisse](https://developers.openai.com/api/docs/guides/live-delegation#send-the-right-kind-of-update), [Responses-Ergebnisse](https://developers.openai.com/api/docs/guides/live-delegation#return-tool-results-and-approvals)

Ein stiller Kontext kann spätere gesprochene Antworten beeinflussen. Geheimnisse und private interne Überlegungen verbleiben im Backend. Fremde Seiteninhalte und Tool-Daten als Faktenkontext behandeln. Vertrauenswürdige Verhaltensanweisungen gezielt übermitteln.

## Gespräch eröffnen und Stille steuern

Für eine Begrüßung durch den Agenten beim Start eine `developer`-Nachricht in `session.input` setzen. Darin Sprache, Begrüßung und anschließendes Zuhören festlegen. Nach `session.started` dieselbe Anweisung einmal über `session.commentary.append` mit eindeutiger Ereignis-ID und `delegation_id: null` senden. Eingehendes Audio aktiv halten. Danach Ausgabeaudio, Transkript und Wiedergabe prüfen. Ein Append-Acknowledgment bestätigt die Kontextzustellung. Hörbare Ausführung und genauer Wortlaut benötigen eigene Nachweise. Bei zwingendem Wortlaut einen geprüften Clip und die Wiedergabesteuerung der Anwendung verwenden. [Begrüßungsablauf](https://developers.openai.com/api/docs/guides/live-conversations#greet-before-the-caller-speaks)

Client-Delegation bietet eine Verzögerung automatischer Bestätigungen über `acknowledgement_delay_ms`. Ein rechtzeitiges Thinking- oder Commentary-Append kann ausstehende automatische Bestätigungen unterdrücken. Dies wirkt sessionweit auf alle noch ausstehenden Bestätigungen. Bereits erzeugte Audioausgabe und eigenständiges Sprechen sind davon gesondert zu behandeln. Wenn Stille garantiert werden muss, steuert die Anwendung die Wiedergabe. Diese Mechanik nur bei entsprechendem Produktbedarf ergänzen. [Automatische Bestätigungen](https://developers.openai.com/api/docs/guides/live-delegation#suppress-automatic-acknowledgments-while-tools-run)

## Änderungen laufender Aufgaben

Die Anwendung hält den aktuellen Auftrag, seine Version, die Operation und das tatsächliche Ergebnis zusammen. Nach einer Korrektur werden veraltete Ergebnisse verworfen oder mit dem bereits ausgeführten Zustand abgeglichen. Bereits erledigte Aktionen bleiben bei der Entscheidung über den nächsten Schritt relevant.

Bei einer Bitte, das Sprechen zu stoppen, gibt GPT-Live das Wort ab. Ein Änderungs- oder Abbruchauftrag muss das Backend erreichen. Laufende Arbeit, bereits erfolgte Änderungen und ausstehende Bestätigungen werden dort abgeglichen. Vor einem Retry nach unklarer Antwort prüfen, ob die Aktion bereits ausgeführt wurde. Abbruch und Erfolg erst nach bestätigtem Ergebnis melden. [Korrekturen und Fortschritt](https://developers.openai.com/api/docs/guides/live-delegation#keep-updates-accurate-and-useful)

Ein Auflegen oder Weiterverbinden benötigt eine implementierte Fähigkeit. Wenn diese fehlt, benenne die offene Voraussetzung für genau diesen Teil des Produkts. Vorhandene Regeln für Abschied, Wiedergabeende, Verbindungsabbau und laufende Arbeit beim Entwurf erhalten. [Migration und Aktionsgrenzen](https://developers.openai.com/api/docs/guides/live-migration?migration-path=realtime#split-conversation-and-backend-instructions)
