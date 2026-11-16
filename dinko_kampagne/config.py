"""Konfiguration der Dinko-Kampagne. Keine Zugangsdaten, keine Kandidatendaten.

Kampagnen-Fakten stammen aus `outputs/dinko-v2/Dinko Pet 13 v2 Steuerung.xlsx` (dort als
bestätigt markiert). Ausnahme: „Smještaj je plaćen“ nach Angabe des Auftraggebers vom
16.11.2026; in der Excel-Steuerung stand das bis dahin als nicht bestätigt.
"""

from __future__ import annotations

import os
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

VERSION = "kampagne-1.0.0"
CAMPAIGN_ID = "dinko-tiefbau-2026-11"

TIMEZONE = "Europe/Sarajevo"
TZ = ZoneInfo(TIMEZONE)

AGENT_NAME = os.getenv("DINKO_AGENT_NAME", "dinko-kampagne")

# --- Airtable: Basis „GIG Casting“, Tabelle „Dinko – Kandidati“ -----------------------------
BASE_ID = "appz3VFomHaWhuILV"
T_KANDIDATI = "tbl7UjnrJQXGzFPKH"


class F:
    """Feld-IDs der Tabelle „Dinko – Kandidati“."""

    IME_PREZIME = "fldHp5uj6eH1MaNnT"
    IME = "fld5Czg92Vpzcnphf"
    PREZIME = "fldWClwIbF6pOUi0R"
    KVALIFIKACIJA = "fldqo8or0Zd3VkUao"  # Ausbildung laut CRM, keine Berufserfahrung
    VOZACKA = "fldXqec7XoVVS7K0Q"
    VOZACKE_KATEGORIJE = "fldIwqHRRn9dfEAYt"
    DNC = "fldwb5woIx3HQWSWv"
    DINKO_STATUS = "fldAKXa0Z2ZRWMWdK"
    ISHOD = "fldrpzAxEGBzpa3sc"
    MOZE_NA_CASTING = "fldeTeMFVZbFbL7tE"
    ODGOVORI = "fldA3iq8pkDAFKtGx"
    NAPOMENA = "fld3hIQa6jtQxAbY5"
    ZELJENI_TEKST = "fld8y3cPv7i2DsfDl"
    ZELJENI_VRIJEME = "fldY1mEQrndxzWMyS"
    LINK_TRANSKRIPT = "fldLGu1bjmvlgJdy6"


# Werte des Feldes „Dinko status“, die der Agent am Ende des Anrufs setzt.
STATUS_RAZGOVOR = "razgovor obavljen"
STATUS_NIJE_SE_JAVIO = "nije se javio"
STATUS_GOVORNA_POSTA = "govorna pošta"

# Werte des Feldes „Ishod“.
INTERES_U_TOKU = "interes_u_toku"
ISHODI = (
    INTERES_U_TOKU,
    "zainteresovan_moze",
    "zainteresovan_ne_moze",
    "nije_zainteresovan",
    "kasniji_poziv",
    "pogresna_osoba",
    "ne_zovite_vise",
    "nejasno",
)
ZAVRSNI_ISHODI = tuple(i for i in ISHODI if i != INTERES_U_TOKU)

# --- Termine -------------------------------------------------------------------------------


def _datum(env: str, standard: date) -> date:
    v = os.getenv(env, "").strip()
    return date.fromisoformat(v) if v else standard


def _zeitpunkt(env: str, standard: datetime) -> datetime:
    v = os.getenv(env, "").strip()
    if not v:
        return standard
    dt = datetime.fromisoformat(v)
    return dt.replace(tzinfo=TZ) if dt.tzinfo is None else dt.astimezone(TZ)


CASTING_DATUM = _datum("DINKO_CASTING_DATE", date(2026, 11, 18))
CASTING_MJESTO = "u Bihaću"

# Spätester Zeitpunkt, zu dem ein Kollege zurückrufen kann (Annahme, siehe README).
ROK_POZIVA_KOLEGE = _zeitpunkt(
    "DINKO_CALLBACK_DEADLINE", datetime(2026, 11, 17, 19, 30, tzinfo=TZ)
)
# Zeitfenster, in dem Rückrufe möglich sind (gleich wie Dinkos Anrufzeit).
POZIV_OD = time(9, 0)
POZIV_DO = time(19, 30)

# --- Kampagnen-Fakten (Text für den Kontext, bosnisch, Zahlen ausgeschrieben) ---------------
CAMPAIGN = {
    "pitch": (
        "Radi se o poslu u Njemačkoj, na izgradnji optičke mreže. Radi se na otvorenom: "
        "kopanje rovova, polaganje kablova i rad s građevinskim mašinama."
    ),
    "benefits": (
        "Plata je od četiri hiljade sedamsto pedeset do pet hiljada sto devedeset eura "
        "bruto mjesečno, s dnevnicama. Smještaj je plaćen, prevoz do gradilišta je "
        "organizovan. Radi se četiri sedmice, pa si sedmicu kod kuće."
    ),
    "more_facts": (
        "Ugovor na neodređeno. Trideset dana godišnjeg odmora. Oko osam sati rada dnevno. "
        "Smještaj je zajednički. Njemački jezik nije uslov. Početak rada je prvog marta "
        "dvije hiljade dvadeset sedme."
    ),
    "net_note": (
        "Okvirno tri hiljade dvjesto do tri hiljade četiristo pedeset eura neto, za poresku "
        "klasu jedan, bez braka i djece. Iznos nije garantovan."
    ),
    "casting_description": "Casting uključuje praktični test i razgovor.",
    "travel_cost": "Troškove dolaska na casting snosi kandidat.",
}

# Voraussetzungsfragen. Vorbelegung, der Auftraggeber legt die endgültigen zwei bis drei fest.
PITANJA = (
    "Šta si do sada radio, i imaš li iskustva na gradilištu ili u niskogradnji?",
    "Koliko dugo si radio te poslove?",
)
# Entfällt, wenn der Führerschein schon aus dem CRM bekannt ist.
PITANJE_VOZACKA = "Imaš li vozačku dozvolu, i koje kategorije?"
