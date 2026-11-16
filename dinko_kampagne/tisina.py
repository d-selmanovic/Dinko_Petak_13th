"""Stille-Behandlung: einmal nachfragen, dann auflegen.

LiveKit meldet `user_state_changed` mit `new_state == "away"`, wenn Kandidat und Dinko
`user_away_timeout` Sekunden lang beide schweigen. Der Zustand bleibt „away“, bis der
Kandidat wieder spricht; ein zweites Ereignis kommt von selbst nicht. Deshalb wartet diese
Klasse nach der Nachfrage selbst und legt auf, wenn weiter niemand spricht.

Ohne LiveKit-Abhängigkeit, damit die Logik mit der Standardbibliothek testbar ist.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger("dinko.tisina")


class Tisina:
    def __init__(
        self,
        *,
        nachfragen: Callable[[], Awaitable[None]],
        auflegen: Callable[[str], None],
        nach_s: float = 8.0,
        max_nachfragen: int = 2,
        gespraech_fertig: Callable[[], bool] = lambda: False,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._nachfragen = nachfragen
        self._auflegen = auflegen
        self._nach_s = nach_s
        self._max = max_nachfragen
        self._fertig = gespraech_fertig
        self._sleep = sleep
        self.aktiv = False  # erst nach der Anrufbeantworter-Erkennung
        self.nachfragen_bisher = 0
        self._gesprochen = False
        self._aufgelegt = False
        self._tasks: set[asyncio.Task[None]] = set()

    def aktiviere(self) -> None:
        self.aktiv = True

    def user_state(self, new_state: str) -> asyncio.Task[None] | None:
        """Für jedes `user_state_changed` aufrufen. Gibt die gestartete Aufgabe zurück."""
        if new_state == "speaking":
            self._gesprochen = True
            return None
        if new_state != "away" or not self.aktiv or self._aufgelegt:
            return None
        if self._fertig():
            # Ergebnis steht fest und es ist still: Abschied ist vorbei, Leitung freigeben.
            self._ende("silence after outcome")
            return None
        if self.nachfragen_bisher >= self._max:
            self._ende("silence")
            return None
        self.nachfragen_bisher += 1
        self._gesprochen = False
        task = asyncio.create_task(self._ablauf())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def _ablauf(self) -> None:
        try:
            await self._nachfragen()
        except Exception:
            logger.exception("Nachfrage bei Stille fehlgeschlagen")
        await self._sleep(self._nach_s)
        if not self._gesprochen:
            self._ende("silence")

    def _ende(self, grund: str) -> None:
        if self._aufgelegt:
            return
        self._aufgelegt = True
        logger.info("Stille – auflegen (%s)", grund)
        self._auflegen(grund)
