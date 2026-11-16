"""Dinko als LiveKit-Agent für die Kampagne: ein Tool zum Eintragen des Ergebnisses.

Auflegen übernimmt EndCallTool (end_call). Vergisst das Modell end_call nach einem
abschließenden Ergebnis, legt der Code nach einer Wartezeit selbst auf.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Literal

from livekit.agents import Agent, RunContext, function_tool

from . import zeit
from .airtable import Store
from .ishod import Stanje, obradi_ishod

logger = logging.getLogger("dinko.agent")

# Sekunden bis zum Auflegen durch den Code, wenn das Modell end_call nicht aufruft.
PREKID_POSLIJE_ISHODA = 30.0
PREKID_POSLIJE_GRESKE = 20.0

Ishod = Literal[
    "interes_u_toku",
    "zainteresovan_moze",
    "zainteresovan_ne_moze",
    "nije_zainteresovan",
    "kasniji_poziv",
    "pogresna_osoba",
    "ne_zovite_vise",
    "nejasno",
]


class DinkoKampagne(Agent):
    def __init__(
        self, *, instructions: str, stanje: Stanje, store: Store, tools: list | None = None
    ) -> None:
        super().__init__(instructions=instructions, tools=list(tools or []))
        self._stanje = stanje
        self._store = store
        self._prekid: asyncio.Task[None] | None = None

    def _zakazi_prekid(self, context: RunContext, sekunde: float) -> None:
        """Sicherheitsnetz: nach dem Abschied auflegen, auch wenn end_call ausbleibt."""
        if self._prekid is not None and not self._prekid.done():
            self._prekid.cancel()

        async def _poklopi() -> None:
            await asyncio.sleep(sekunde)
            logger.info("prekid poziva poslije %.0f s bez end_call", sekunde)
            try:
                context.session.shutdown(drain=True)
            except Exception:
                logger.exception("prekid poziva nije uspio")

        self._prekid = asyncio.create_task(_poklopi())

    @function_tool
    async def record_outcome(
        self,
        context: RunContext,
        ishod: Ishod,
        moze_na_casting: Literal["da", "ne", "nepoznato", ""] = "",
        odgovori: str = "",
        napomena_za_kolegu: str = "",
        zeljeni_poziv: str = "",
        zeljeni_dan: str = "",
        zeljeni_sat: str = "",
    ) -> str:
        """Zabilježi stanje ili ishod poziva. Može se pozvati više puta, važi posljednji upis.

        Args:
            ishod: Stanje poziva. interes_u_toku čim osoba prvi put iskaže interes; ostale
                vrijednosti su konačni ishod.
            moze_na_casting: Može li osoba doći na casting: da, ne ili nepoznato.
            odgovori: Odgovori na pitanja o uslovima, onako kako ih je osoba rekla.
            napomena_za_kolegu: Jedna do dvije rečenice za kolegu koji zove.
            zeljeni_poziv: Kada osoba želi poziv kolege, doslovno kako je rekla. Prazno
                znači da kolega zove odmah.
            zeljeni_dan: Dan željenog poziva ako je jasan: danas, sutra, prekosutra ili
                naziv dana u sedmici.
            zeljeni_sat: Sat željenog poziva ako je jasan, na primjer 10:00.
        """
        stanje = self._stanje
        try:
            polja, poruka, otvoreno = obradi_ishod(
                stanje,
                zeit.sada(),
                ishod=ishod,
                moze_na_casting=moze_na_casting,
                odgovori=odgovori,
                napomena_za_kolegu=napomena_za_kolegu,
                zeljeni_poziv=zeljeni_poziv,
                zeljeni_dan=zeljeni_dan,
                zeljeni_sat=zeljeni_sat,
            )
            await self._store.azuriraj(stanje.record_id, polja)
        except Exception:
            logger.exception("record_outcome nije uspio (record %s)", stanje.record_id)
            self._zakazi_prekid(context, PREKID_POSLIJE_GRESKE)
            return (
                "Upis nije uspio. Ne spominji grešku kandidatu. Neka se glasovni model "
                "ljubazno pozdravi, zatim pozovi end_call."
            )
        if not (ishod == "interes_u_toku" and stanje.zavrsen()):
            stanje.ishod = ishod
        logger.info("record_outcome: %s (record %s)", ishod, stanje.record_id)
        if stanje.zavrsen() and not otvoreno:
            self._zakazi_prekid(context, PREKID_POSLIJE_ISHODA)
        return poruka
