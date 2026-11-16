"""Datum und Uhrzeit für die Kampagne. Der Code rechnet, das Modell nicht.

`DINKO_NOW` (ISO, z. B. 2026-11-16T10:15) fixiert die Uhr für Tests.
"""

from __future__ import annotations

import os
import re
from datetime import date, datetime, timedelta

from .config import (
    CASTING_DATUM,
    CASTING_MJESTO,
    POZIV_DO,
    POZIV_OD,
    ROK_POZIVA_KOLEGE,
    TZ,
)

U_DAN = (
    "u ponedjeljak",
    "u utorak",
    "u srijedu",
    "u četvrtak",
    "u petak",
    "u subotu",
    "u nedjelju",
)
MJESEC_GENITIV = (
    "januara",
    "februara",
    "marta",
    "aprila",
    "maja",
    "juna",
    "jula",
    "augusta",
    "septembra",
    "oktobra",
    "novembra",
    "decembra",
)
_JEDINICE = (
    "prvog",
    "drugog",
    "trećeg",
    "četvrtog",
    "petog",
    "šestog",
    "sedmog",
    "osmog",
    "devetog",
)
_DO_DVADESET = (
    *_JEDINICE,
    "desetog",
    "jedanaestog",
    "dvanaestog",
    "trinaestog",
    "četrnaestog",
    "petnaestog",
    "šesnaestog",
    "sedamnaestog",
    "osamnaestog",
    "devetnaestog",
    "dvadesetog",
)
_SAT = (
    "jedan",
    "dva",
    "tri",
    "četiri",
    "pet",
    "šest",
    "sedam",
    "osam",
    "devet",
    "deset",
    "jedanaest",
    "dvanaest",
)
# Wochentage ohne diakritische Zeichen, Nominativ und Akkusativ.
_DANI = {
    "ponedjeljak": 0,
    "utorak": 1,
    "srijeda": 2,
    "srijedu": 2,
    "cetvrtak": 3,
    "petak": 4,
    "subota": 5,
    "subotu": 5,
    "nedjelja": 6,
    "nedjelju": 6,
}
_BEZ_KVACICA = str.maketrans("čćšžđ", "ccszd")


def sada() -> datetime:
    fiks = os.getenv("DINKO_NOW", "").strip()
    if fiks:
        dt = datetime.fromisoformat(fiks)
        return dt.replace(tzinfo=TZ) if dt.tzinfo is None else dt.astimezone(TZ)
    return datetime.now(TZ)


def redni_dan(dan: int) -> str:
    """Tag des Monats im Genitiv, z. B. 18 → „osamnaestog“."""
    if not 1 <= dan <= 31:
        raise ValueError("Tag außerhalb 1–31")
    if dan <= 20:
        return _DO_DVADESET[dan - 1]
    if dan == 30:
        return "tridesetog"
    zehner = "dvadeset" if dan < 30 else "trideset"
    return f"{zehner} {_JEDINICE[dan % 10 - 1]}"


def datum_rijecima(d: date) -> str:
    return f"{redni_dan(d.day)} {MJESEC_GENITIV[d.month - 1]}"


def relativni_dan(cilj: date, danas: date) -> str:
    return {0: "danas", 1: "sutra", 2: "prekosutra"}.get((cilj - danas).days, "")


def sat_rijecima(h: int, m: int) -> str:
    """19:30 → „pola osam navečer“, 10:00 → „deset ujutro“. Andere Minuten als Ziffern."""
    if h == 12 and m == 0:
        return "podne"
    dio = "ujutro" if h < 12 else ("popodne" if h < 18 else "navečer")
    h12 = h % 12 or 12
    if m == 0:
        return f"{_SAT[h12 - 1]} {dio}"
    if m == 30:
        return f"pola {_SAT[h12 % 12]} {dio}"
    return f"{h}:{m:02d}"


def casting_passed(now: datetime) -> bool:
    """Am Casting-Tag selbst wird nicht mehr eingeladen."""
    return now.astimezone(TZ).date() >= CASTING_DATUM


def casting_phrase(now: datetime) -> str:
    """Fertiger Satzteil zum Casting-Termin, passend zum Anruftag."""
    rel = relativni_dan(CASTING_DATUM, now.astimezone(TZ).date())
    teile = [
        rel,
        U_DAN[CASTING_DATUM.weekday()],
        datum_rijecima(CASTING_DATUM),
        CASTING_MJESTO,
    ]
    return ", ".join(t for t in teile if t)


def callback_deadline_phrase(now: datetime) -> str:
    """Spätester Rückruf des Kollegen, z. B. „sutra, u utorak, do pola osam navečer“.

    Leer, wenn der Zeitpunkt schon vorbei ist.
    """
    now = now.astimezone(TZ)
    rok = ROK_POZIVA_KOLEGE
    if now >= rok:
        return ""
    sat = sat_rijecima(rok.hour, rok.minute)
    rel = relativni_dan(rok.date(), now.date())
    if rel == "danas":
        return f"danas do {sat}"
    teile = [rel, U_DAN[rok.weekday()]]
    return ", ".join(t for t in teile if t) + f", do {sat}"


def _sat_minuta(sat: str) -> tuple[int, int] | None:
    s = sat.strip().lower().replace("sati", "").replace("h", ":").strip(" :")
    m = re.fullmatch(r"(\d{1,2})(?:[:.](\d{2}))?", s)
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2) or 0)
    return (h, mi) if h <= 23 and mi <= 59 else None


def zeljeno_vrijeme(dan: str, sat: str, now: datetime) -> datetime | None:
    """Wunschzeit des Kandidaten als Zeitpunkt. None, wenn Tag oder Uhrzeit unklar sind.

    dan: danas, sutra, prekosutra, Wochentag oder ISO-Datum. sat: 10, 10:30, 10h, 10.30.
    """
    now = now.astimezone(TZ)
    hm = _sat_minuta(sat)
    if hm is None:
        return None
    d = dan.strip().lower().translate(_BEZ_KVACICA).removeprefix("u ").strip()
    if d in ("danas", "sutra", "prekosutra"):
        tag = now.date() + timedelta(days=("danas", "sutra", "prekosutra").index(d))
    elif d in _DANI:
        tag = now.date() + timedelta(days=(_DANI[d] - now.weekday()) % 7)
    else:
        try:
            tag = date.fromisoformat(d)
        except ValueError:
            return None
    return datetime(tag.year, tag.month, tag.day, hm[0], hm[1], tzinfo=TZ)


def provjeri_zeljeno(dt: datetime, now: datetime) -> str:
    """„ok“, „proslo“, „poslije_roka“ oder „van_vremena“ (außerhalb 09:00–19:30)."""
    dt, now = dt.astimezone(TZ), now.astimezone(TZ)
    if dt <= now:
        return "proslo"
    if dt > ROK_POZIVA_KOLEGE:
        return "poslije_roka"
    if not POZIV_OD <= dt.time() <= POZIV_DO:
        return "van_vremena"
    return "ok"
