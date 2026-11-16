"""Airtable-Zugriff für die Tabelle „Dinko – Kandidati“: ein Datensatz lesen, ein Datensatz
ändern. Keine Personendaten in Logs, nur Record-IDs und Statuscodes.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any, Protocol

from .config import BASE_ID, T_KANDIDATI

logger = logging.getLogger("dinko.airtable")

Fields = dict[str, Any]
_RECORD_ID = re.compile(r"rec[A-Za-z0-9]{14}")


def gueltige_record_id(record_id: str) -> bool:
    return bool(_RECORD_ID.fullmatch(record_id or ""))


class Store(Protocol):
    async def ucitaj(self, record_id: str) -> Fields: ...
    async def azuriraj(self, record_id: str, fields: Fields) -> None: ...


class AirtableStore:
    """Liest und schreibt mit Feld-IDs. Token aus AIRTABLE_API_KEY."""

    def __init__(self, token: str | None = None, timeout: float = 8.0) -> None:
        self._token = token or os.environ["AIRTABLE_API_KEY"]
        self._timeout = timeout

    def _url(self, record_id: str) -> str:
        if not gueltige_record_id(record_id):
            raise ValueError("Ungültige Record-ID")
        return f"https://api.airtable.com/v0/{BASE_ID}/{T_KANDIDATI}/{record_id}"

    async def _req(self, method: str, url: str, **kw: Any) -> dict[str, Any]:
        import aiohttp

        headers = {"Authorization": f"Bearer {self._token}"}
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        for versuch in (1, 2):
            async with (
                aiohttp.ClientSession(timeout=timeout, headers=headers) as s,
                s.request(method, url, **kw) as r,
            ):
                if r.status in (429, 500, 502, 503) and versuch == 1:
                    logger.warning("Airtable %s, zweiter Versuch", r.status)
                    await asyncio.sleep(1.5)
                    continue
                if r.status >= 400:
                    raise RuntimeError(f"Airtable {method} fehlgeschlagen: {r.status}")
                return await r.json()
        raise RuntimeError("Airtable nicht erreichbar")

    async def ucitaj(self, record_id: str) -> Fields:
        daten = await self._req(
            "GET", self._url(record_id), params={"returnFieldsByFieldId": "true"}
        )
        return dict(daten.get("fields") or {})

    async def azuriraj(self, record_id: str, fields: Fields) -> None:
        if not fields:
            return
        await self._req(
            "PATCH", self._url(record_id), json={"fields": fields, "typecast": True}
        )


class FakeStore:
    """Für Tests: hält einen Datensatz im Speicher und merkt sich alle Änderungen."""

    def __init__(self, fields: Fields | None = None, *, fehler: bool = False) -> None:
        self.fields: Fields = dict(fields or {})
        self.aenderungen: list[Fields] = []
        self.fehler = fehler

    async def ucitaj(self, record_id: str) -> Fields:
        return dict(self.fields)

    async def azuriraj(self, record_id: str, fields: Fields) -> None:
        if self.fehler:
            raise RuntimeError("Airtable PATCH fehlgeschlagen: 500")
        self.aenderungen.append(dict(fields))
        self.fields.update(fields)
