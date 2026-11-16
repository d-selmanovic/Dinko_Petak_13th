"""Ergebnis eines Anrufs: Zustand und Abbildung auf Airtable-Felder. Ohne Netzwerk, testbar."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from . import zeit
from .config import (
    INTERES_U_TOKU,
    ISHODI,
    STATUS_GOVORNA_POSTA,
    STATUS_NIJE_SE_JAVIO,
    STATUS_RAZGOVOR,
    ZAVRSNI_ISHODI,
    F,
)

MAX_TEKST = 2000


@dataclass
class Stanje:
    """Zustand eines Anrufs. Enthält keine Telefonnummer."""

    record_id: str
    ishod: str | None = None
    amd: str = ""  # Kategorie der Anrufbeantworter-Erkennung
    kandidat_govorio: bool = False
    dinko_govorio: bool = False
    sacuvano: bool = False
    upisi: list[dict[str, Any]] = field(default_factory=list)  # nur für Tests/Logs

    def zavrsen(self) -> bool:
        return self.ishod in ZAVRSNI_ISHODI


def _tekst(v: str | None) -> str:
    return (v or "").strip()[:MAX_TEKST]


def obradi_ishod(
    stanje: Stanje,
    now: datetime,
    *,
    ishod: str,
    moze_na_casting: str = "",
    odgovori: str = "",
    napomena_za_kolegu: str = "",
    zeljeni_poziv: str = "",
    zeljeni_dan: str = "",
    zeljeni_sat: str = "",
) -> tuple[dict[str, Any], str, bool]:
    """Baut die Airtable-Felder für einen Eintrag und die Rückmeldung an das Backend-Modell.

    Rückgabe: (Felder, Rückmeldung, offen). `offen` heißt: Das Gespräch muss noch etwas
    klären (z. B. eine andere Rückrufzeit), es darf noch nicht aufgelegt werden.
    Verändert `stanje` nicht; das geschieht erst nach erfolgreichem Schreiben.
    """
    if ishod not in ISHODI:
        raise ValueError(f"Unbekannter ishod: {ishod}")
    polja: dict[str, Any] = {}
    napomene: list[str] = []

    # Ein abgeschlossenes Ergebnis wird nicht auf „Interesse läuft“ zurückgestuft.
    if not (ishod == INTERES_U_TOKU and stanje.zavrsen()):
        polja[F.ISHOD] = ishod
    if moze_na_casting in ("da", "ne", "nepoznato"):
        polja[F.MOZE_NA_CASTING] = moze_na_casting
    if t := _tekst(odgovori):
        polja[F.ODGOVORI] = t
    if t := _tekst(napomena_za_kolegu):
        polja[F.NAPOMENA] = t
    if ishod == "ne_zovite_vise":
        polja[F.DNC] = True

    if t := _tekst(zeljeni_poziv):
        polja[F.ZELJENI_TEKST] = t
    if _tekst(zeljeni_dan) and _tekst(zeljeni_sat):
        dt = zeit.zeljeno_vrijeme(zeljeni_dan, zeljeni_sat, now)
        stand = zeit.provjeri_zeljeno(dt, now) if dt else "nejasno"
        if stand == "ok":
            polja[F.ZELJENI_VRIJEME] = dt.isoformat(timespec="minutes")
            polja.setdefault(F.ZELJENI_TEKST, f"{zeljeni_dan} {zeljeni_sat}".strip())
        elif stand == "poslije_roka":
            rok = zeit.callback_deadline_phrase(now) or "prije castinga"
            napomene.append(
                "Traženo vrijeme je prekasno: kolega mora nazvati najkasnije "
                f"{rok}. Vrijeme nije zabilježeno, pitaj za ranije vrijeme."
            )
        elif stand == "van_vremena":
            napomene.append(
                "Kolege zovu između devet ujutro i pola osam navečer. Vrijeme nije "
                "zabilježeno, pitaj za vrijeme u tom rasponu."
            )
        else:
            napomene.append(
                "Dan ili sat poziva nisu jasni ili su već prošli. Vrijeme nije "
                "zabilježeno, pitaj još jednom kratko."
            )
    elif ishod == "kasniji_poziv" and not _tekst(zeljeni_poziv):
        napomene.append("Vrijeme poziva nije navedeno. Pitaj kada da kolega nazove.")

    return polja, " ".join(["Zabilježeno.", *napomene]), bool(napomene)


def zavrsna_polja(stanje: Stanje, link_transkript: str | None) -> dict[str, Any]:
    """Felder, die der Agent beim Ende des Anrufs setzt."""
    if stanje.amd == "machine-vm":
        status = STATUS_GOVORNA_POSTA
    elif stanje.amd == "machine-unavailable":
        status = STATUS_NIJE_SE_JAVIO
    elif stanje.kandidat_govorio or stanje.ishod:
        status = STATUS_RAZGOVOR
    else:
        status = STATUS_NIJE_SE_JAVIO
    polja: dict[str, Any] = {F.DINKO_STATUS: status}
    if status == STATUS_RAZGOVOR and stanje.ishod is None:
        polja[F.ISHOD] = "nejasno"
    if link_transkript:
        polja[F.LINK_TRANSKRIPT] = link_transkript
    return polja
