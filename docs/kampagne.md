# Dinko-Kampagne: Casting Bihać, Mittwoch 18.11.2026

Kurzer ausgehender Anruf an frühere JobStep-Bewerber: Stelle vorstellen, Interesse und
Teilnahme am Casting klären, zwei bis drei Voraussetzungen fragen, Rückruf eines Kollegen
ankündigen. Keine Weiterleitung in dieser Version.

Der v2-Code (`dinko_v2_*.py`) ist unverändert. Die Kampagne liegt in `dinko_kampagne/`,
Einstieg ist `dinko_kampagne_livekit.py`, Agent-Name `dinko-kampagne`.

## Stand der Prüfung

Geprüft: Datumslogik, Wunschzeit, Abbildung auf Airtable-Felder, Pflichtüberschriften der
Prompts, Registrierung der Tools, Import des Einstiegs mit `livekit-agents==1.8.12`
(`python3 -m unittest discover -s tests`).

Nicht geprüft: echter Anruf, Anrufbeantworter-Erkennung, Auflegen, Stimme, Docker-Build,
Schreiben in die echte Airtable-Tabelle, Transkript-Ablage, Langfuse. Das zeigt erst ein
Testanruf.

## Ablauf eines Anrufs

1. Der Wählautomat (n8n) startet den Anruf über LiveKit und übergibt
   `{"record_id": "rec..."}` als Dispatch-Metadaten. Der Agent wählt nicht selbst.
2. Der Agent liest den Datensatz aus Airtable. Ins Modell gehen nur Vorname, Nachname,
   Beruf und die Kampagnen-Fakten, keine Telefonnummer.
3. Dinko wartet, bis sich jemand meldet (Anrufbeantworter-Erkennung). Bei Mailbox: kurze
   Nachricht, dann auflegen.
4. Das Backend-Modell trägt das Ergebnis mit `record_outcome` ein, zuerst
   `interes_u_toku`, am Ende das abschließende Ergebnis, und legt mit `end_call` auf.
5. Am Ende schreibt der Agent `Dinko status` und den Transkript-Link und löscht den Raum.
   Damit ist die Leitung frei.

Sicherheitsnetze im Code:

- Bleibt Dinko nach dem Abheben still, begrüßt der Code nach 4 Sekunden
  (`DINKO_GREETING_FALLBACK_S`, 0 schaltet es ab).
- Ruft das Modell `end_call` nicht auf, legt der Code 30 Sekunden nach dem abschließenden
  Ergebnis auf.
- Datum und Uhrzeit rechnet der Code (`dinko_kampagne/zeit.py`), nicht das Modell.

## Airtable

Basis „GIG Casting“, Tabelle „Dinko – Kandidati“ (`tbl7UjnrJQXGzFPKH`).

| Wer | Schreibt |
|---|---|
| Import | `Ime`, `Prezime`, `Telefon (E.164)`, `Zanimanje`, `Redoslijed poziva`, `Poziv odobren` |
| Wählautomat (n8n) | `Dinko status` = „u toku“, `Broj pokušaja`, `Zadnji poziv`, `Sljedeći pokušaj`, `Pokušaj ID` |
| Agent im Gespräch | `Ishod`, `Može na casting`, `Odgovori`, `Napomena za kolegu`, `Željeni poziv (tekst)`, `Željeni poziv (vrijeme)`, `Ne zovi (DNC)` |
| Agent am Ende | `Dinko status` (razgovor obavljen / nije se javio / govorna pošta), `Link transkript`, `Ishod` = „nejasno“, falls gesprochen wurde und nichts eingetragen ist |
| Meldung (n8n) | `Obavijest poslana`, `Obavijest poslana (vrijeme)`, `Podsjetnik poslan` |
| Kollege | `Kolega preuzeo`, `Rezultat kolege` |

## Meldung an die Kollegen (n8n)

Bedingung: `Ishod` ist `interes_u_toku`, `zainteresovan_moze` oder `kasniji_poziv`,
`Dinko status` ist nicht „u toku“ (das Gespräch ist beendet) und `Obavijest poslana` ist
leer. Die Meldung geht also erst nach dem Gespräch hinaus: Der Kollege ruft nicht an,
während der Kandidat noch mit Dinko spricht, und die Wunschzeit steht schon fest.

`Željeni poziv (vrijeme)` leer = jetzt anrufen. Gefüllt = zu dieser Zeit anrufen, mit einer
Erinnerung kurz vorher.

## Rückrufzeit

Standard: Kollege ruft in den nächsten Minuten an. Nennt der Kandidat eine andere Zeit,
gilt seine Zeit. Der Code nimmt nur Zeiten an, die in der Zukunft liegen, zwischen 09:00
und 19:30 und vor `DINKO_CALLBACK_DEADLINE` (Standard Dienstag 17.11.2026, 19:30; Annahme,
vom Auftraggeber noch nicht bestätigt). Sonst bekommt Dinko den Hinweis, nach einer anderen
Zeit zu fragen.

## Deployment in LiveKit Cloud

Dinko nutzt die Telefonleitung von Lina, läuft also als eigener Agent im Projekt
`lina-oai`. Secrets des Agents (Namen in `.env.example`): `OPENAI_API_KEY`,
`AIRTABLE_API_KEY`, `R2_*`, `LANGFUSE_*`, optional `DINKO_VOICE_ID`. Ohne `R2_*` gibt es
kein Transkript, ohne `LANGFUSE_*` kein Tracing; der Anruf läuft trotzdem.

Die Anrufbeantworter-Erkennung und die Rauschunterdrückung laufen über LiveKit Cloud.

Angelegt am 16.11.2026: Agent-ID `CA_g54xPLuXH2bE`, Projekt `lina-oai-kk6g8p5z`, Region
eu-central. `lk agent create` hat dabei lokal eine `livekit.toml` geschrieben; sie steht in
`.gitignore` und bleibt auf dem Rechner, von dem deployt wird. Neuer Stand:
`git pull`, dann `lk agent deploy`.

## Offen

- Voraussetzungsfragen (`PITANJA` in `config.py`) sind vorbelegt, nicht endgültig.
- Casting-Uhrzeit und Adresse nennt der Kollege.
- Weiterleitung an einen Kollegen kommt mit dem nächsten Update.
