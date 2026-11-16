"""Tests der Dinko-Kampagne. Nur Standardbibliothek; die LiveKit-Tests werden übersprungen,
wenn die LiveKit-Pakete nicht installiert sind.

Ausführen:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import re
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dinko_kampagne import prompts, zeit  # noqa: E402
from dinko_kampagne.airtable import FakeStore, gueltige_record_id  # noqa: E402
from dinko_kampagne.config import CAMPAIGN, PITANJA, TZ, F  # noqa: E402
from dinko_kampagne.ishod import Stanje, obradi_ishod, zavrsna_polja  # noqa: E402

REC = "recAAAAAAAAAAAAAA"


def am(tag: int, h: int = 10, m: int = 0) -> datetime:
    return datetime(2026, 11, tag, h, m, tzinfo=TZ)


class Zeit(unittest.TestCase):
    def test_casting_phrase_nach_anruftag(self):
        rest = "u srijedu, osamnaestog novembra, u Bihaću"
        self.assertEqual(zeit.casting_phrase(am(16)), f"prekosutra, {rest}")
        self.assertEqual(zeit.casting_phrase(am(17)), f"sutra, {rest}")
        self.assertEqual(zeit.casting_phrase(am(10)), rest)

    def test_casting_vorbei(self):
        self.assertFalse(zeit.casting_passed(am(16)))
        self.assertFalse(zeit.casting_passed(am(17, 19, 30)))
        self.assertTrue(zeit.casting_passed(am(18, 8)))
        self.assertTrue(zeit.casting_passed(am(19)))

    def test_spaetester_rueckruf(self):
        self.assertEqual(
            zeit.callback_deadline_phrase(am(16)), "sutra, u utorak, do pola osam navečer"
        )
        self.assertEqual(
            zeit.callback_deadline_phrase(am(17)), "danas do pola osam navečer"
        )
        self.assertEqual(zeit.callback_deadline_phrase(am(17, 20)), "")

    def test_zahlwoerter(self):
        self.assertEqual(zeit.redni_dan(1), "prvog")
        self.assertEqual(zeit.redni_dan(18), "osamnaestog")
        self.assertEqual(zeit.redni_dan(21), "dvadeset prvog")
        self.assertEqual(zeit.redni_dan(30), "tridesetog")
        self.assertEqual(zeit.redni_dan(31), "trideset prvog")
        self.assertEqual(zeit.sat_rijecima(19, 30), "pola osam navečer")
        self.assertEqual(zeit.sat_rijecima(10, 0), "deset ujutro")
        self.assertEqual(zeit.sat_rijecima(12, 30), "pola jedan popodne")
        self.assertEqual(zeit.sat_rijecima(12, 0), "podne")

    def test_wunschzeit(self):
        now = am(16, 15)
        self.assertEqual(zeit.zeljeno_vrijeme("sutra", "10", now), am(17, 10))
        self.assertEqual(zeit.zeljeno_vrijeme("u utorak", "10:30", now), am(17, 10, 30))
        self.assertEqual(zeit.zeljeno_vrijeme("Danas", "17h", now), am(16, 17))
        self.assertEqual(zeit.zeljeno_vrijeme("četvrtak", "9.15", now), am(19, 9, 15))
        self.assertEqual(zeit.zeljeno_vrijeme("2026-11-17", "14", now), am(17, 14))
        self.assertIsNone(zeit.zeljeno_vrijeme("uskoro", "10", now))
        self.assertIsNone(zeit.zeljeno_vrijeme("sutra", "popodne", now))
        self.assertIsNone(zeit.zeljeno_vrijeme("sutra", "25", now))

    def test_wunschzeit_pruefung(self):
        now = am(16, 15)
        self.assertEqual(zeit.provjeri_zeljeno(am(17, 10), now), "ok")
        self.assertEqual(zeit.provjeri_zeljeno(am(17, 19, 30), now), "ok")
        self.assertEqual(zeit.provjeri_zeljeno(am(16, 9), now), "proslo")
        self.assertEqual(zeit.provjeri_zeljeno(am(17, 21), now), "poslije_roka")
        self.assertEqual(zeit.provjeri_zeljeno(am(18, 10), now), "poslije_roka")
        self.assertEqual(zeit.provjeri_zeljeno(am(17, 8), now), "van_vremena")


class Ishod(unittest.TestCase):
    def test_interesse_sofort(self):
        polja, poruka, offen = obradi_ishod(Stanje(REC), am(16), ishod="interes_u_toku")
        self.assertEqual(polja, {F.ISHOD: "interes_u_toku"})
        self.assertEqual(poruka, "Zabilježeno.")
        self.assertFalse(offen)

    def test_abschluss_mit_antworten(self):
        polja, _, offen = obradi_ishod(
            Stanje(REC),
            am(16),
            ishod="zainteresovan_moze",
            moze_na_casting="da",
            odgovori="  bagerista, pet godina; B i C  ",
            napomena_za_kolegu="Zvati odmah.",
        )
        self.assertEqual(polja[F.ISHOD], "zainteresovan_moze")
        self.assertEqual(polja[F.MOZE_NA_CASTING], "da")
        self.assertEqual(polja[F.ODGOVORI], "bagerista, pet godina; B i C")
        self.assertEqual(polja[F.NAPOMENA], "Zvati odmah.")
        self.assertNotIn(F.ZELJENI_VRIJEME, polja)
        self.assertFalse(offen)

    def test_wunschzeit_gueltig(self):
        polja, _, offen = obradi_ishod(
            Stanje(REC),
            am(16, 15),
            ishod="zainteresovan_moze",
            zeljeni_poziv="sutra u deset",
            zeljeni_dan="sutra",
            zeljeni_sat="10:00",
        )
        self.assertEqual(polja[F.ZELJENI_TEKST], "sutra u deset")
        self.assertEqual(polja[F.ZELJENI_VRIJEME], "2026-11-17T10:00+01:00")
        self.assertFalse(offen)

    def test_wunschzeit_nach_dem_casting(self):
        polja, poruka, offen = obradi_ishod(
            Stanje(REC),
            am(16, 15),
            ishod="zainteresovan_moze",
            zeljeni_poziv="u četvrtak u deset",
            zeljeni_dan="četvrtak",
            zeljeni_sat="10",
        )
        self.assertNotIn(F.ZELJENI_VRIJEME, polja)
        self.assertIn("sutra, u utorak, do pola osam navečer", poruka)
        self.assertTrue(offen)

    def test_wunschzeit_ausserhalb_der_zeiten(self):
        _, poruka, offen = obradi_ishod(
            Stanje(REC), am(16, 15), ishod="kasniji_poziv", zeljeni_dan="sutra", zeljeni_sat="7"
        )
        self.assertIn("između devet ujutro i pola osam navečer", poruka)
        self.assertTrue(offen)

    def test_spaeter_ohne_zeit(self):
        _, poruka, offen = obradi_ishod(Stanje(REC), am(16), ishod="kasniji_poziv")
        self.assertIn("Pitaj kada da kolega nazove", poruka)
        self.assertTrue(offen)

    def test_anrufverbot(self):
        polja, _, _ = obradi_ishod(Stanje(REC), am(16), ishod="ne_zovite_vise")
        self.assertIs(polja[F.DNC], True)

    def test_keine_rueckstufung(self):
        stanje = Stanje(REC, ishod="zainteresovan_moze")
        polja, _, _ = obradi_ishod(stanje, am(16), ishod="interes_u_toku", odgovori="B")
        self.assertNotIn(F.ISHOD, polja)
        self.assertEqual(polja[F.ODGOVORI], "B")

    def test_unbekanntes_ergebnis(self):
        with self.assertRaises(ValueError):
            obradi_ishod(Stanje(REC), am(16), ishod="mozda")

    def test_abschlussfelder(self):
        self.assertEqual(
            zavrsna_polja(Stanje(REC, amd="machine-vm"), None),
            {F.DINKO_STATUS: "govorna pošta"},
        )
        self.assertEqual(
            zavrsna_polja(Stanje(REC, amd="machine-unavailable"), None),
            {F.DINKO_STATUS: "nije se javio"},
        )
        self.assertEqual(
            zavrsna_polja(Stanje(REC), None), {F.DINKO_STATUS: "nije se javio"}
        )
        self.assertEqual(
            zavrsna_polja(Stanje(REC, kandidat_govorio=True), "https://x/t.txt"),
            {
                F.DINKO_STATUS: "razgovor obavljen",
                F.ISHOD: "nejasno",
                F.LINK_TRANSKRIPT: "https://x/t.txt",
            },
        )
        # Abgebrochenes Gespräch nach Interesse: Ergebnis bleibt stehen.
        self.assertEqual(
            zavrsna_polja(Stanje(REC, ishod="interes_u_toku", kandidat_govorio=True), None),
            {F.DINKO_STATUS: "razgovor obavljen"},
        )


class Prompts(unittest.TestCase):
    UEBERSCHRIFTEN = (
        "Backchannel policy:",
        "Interruption policy:",
        "Delegation policy:",
        "Backend tools:",
        "Generate <|SpawnThinking|> when:",
        "Do not generate <|SpawnThinking|> when:",
    )

    def test_pflichtueberschriften_genau_einmal_und_in_reihenfolge(self):
        stellen = []
        for u in self.UEBERSCHRIFTEN:
            self.assertEqual(prompts.VOICE.count("\n" + u + "\n"), 1, u)
            stellen.append(prompts.VOICE.index("\n" + u + "\n"))
        self.assertEqual(stellen, sorted(stellen))

    def test_backend_nennt_die_tools(self):
        self.assertIn("record_outcome", prompts.BACKEND)
        self.assertIn("end_call", prompts.BACKEND)
        self.assertNotIn("record_outcome", prompts.VOICE)

    def test_kontext_ohne_telefon_und_record_id(self):
        polja = {
            F.IME: "Amir",
            F.PREZIME: "Test",
            F.ZANIMANJE: "bagerista",
            "fldHIQHuixlddGmrB": "+38761000000",
        }
        ctx = prompts.kontekst(polja, am(16, 10, 15))
        text = json.dumps(ctx, ensure_ascii=False)
        self.assertNotIn("+387", text)
        self.assertNotIn("rec", ctx["candidate"])
        self.assertEqual(ctx["candidate"]["first_name"], "Amir")
        self.assertEqual(ctx["candidate"]["profession"], "bagerista")
        self.assertEqual(ctx["as_of"], "2026-11-16T10:15+01:00")
        self.assertFalse(ctx["campaign"]["casting_passed"])
        self.assertTrue(ctx["campaign"]["casting_phrase"].startswith("prekosutra"))
        self.assertEqual(ctx["call_questions"], list(PITANJA))

    def test_vorname_aus_vollem_namen(self):
        ctx = prompts.kontekst({F.IME_PREZIME: "Amir Test Primjer"}, am(16))
        self.assertEqual(ctx["candidate"]["first_name"], "Amir")
        self.assertEqual(ctx["candidate"]["last_name"], "Test Primjer")

    def test_nach_dem_casting(self):
        ctx = prompts.kontekst({F.IME: "Amir"}, am(19))
        self.assertTrue(ctx["campaign"]["casting_passed"])
        self.assertEqual(ctx["campaign"]["callback_deadline_phrase"], "")

    def test_zahlen_ausgeschrieben(self):
        for schluessel, text in CAMPAIGN.items():
            self.assertIsNone(re.search(r"\d", text), schluessel)
        for frage in PITANJA:
            self.assertIsNone(re.search(r"\d", frage))

    def test_kontext_haengt_an_beiden_prompts(self):
        ctx = prompts.kontekst({F.IME: "Amir"}, am(16))
        for text in (prompts.voice_instructions(ctx), prompts.backend_instructions(ctx)):
            self.assertIn("DINKO_CONTEXT — podaci za ovaj poziv", text)
            self.assertIn('"first_name": "Amir"', text)


class Airtable(unittest.TestCase):
    def test_record_id(self):
        self.assertTrue(gueltige_record_id(REC))
        for falsch in ("", "rec123", "recAAAAAAAAAAAAAA/../x", "tblAAAAAAAAAAAAAA"):
            self.assertFalse(gueltige_record_id(falsch))

    def test_fake_store(self):
        store = FakeStore({F.IME: "Amir"})
        asyncio.run(store.azuriraj(REC, {F.ISHOD: "nejasno"}))
        self.assertEqual(store.aenderungen, [{F.ISHOD: "nejasno"}])
        self.assertEqual(asyncio.run(store.ucitaj(REC))[F.ISHOD], "nejasno")


class Abhaengigkeiten(unittest.TestCase):
    def test_requirements_txt_enthaelt_die_livekit_versionen(self):
        """Die LiveKit-CLI braucht requirements.txt; die Versionen dürfen nicht auseinanderlaufen."""
        wurzel = Path(__file__).resolve().parents[1]
        alle = (wurzel / "requirements.txt").read_text(encoding="utf-8").split()
        for zeile in (wurzel / "requirements-livekit.txt").read_text(encoding="utf-8").split():
            self.assertIn(zeile, alle)


@unittest.skipUnless(importlib.util.find_spec("livekit"), "LiveKit nicht installiert")
class LiveKit(unittest.TestCase):
    def test_agent_hat_die_tools(self):
        from livekit.agents.beta import EndCallTool

        from dinko_kampagne.agent import DinkoKampagne

        agent = DinkoKampagne(
            instructions="x",
            stanje=Stanje(REC),
            store=FakeStore(),
            tools=[EndCallTool(end_instructions=None, ignore_on_enter=True)],
        )
        namen = set()
        for tool in agent.tools:
            namen.add(getattr(tool, "id", None))
            namen.update(getattr(t, "id", None) for t in getattr(tool, "tools", None) or [])
        self.assertLessEqual({"record_outcome", "end_call"}, namen)

    def test_einstieg_importierbar(self):
        import dinko_kampagne_livekit as einstieg

        self.assertEqual(einstieg.AGENT_NAME, "dinko-kampagne")
        opts = einstieg._responses_options({"candidate": {}})
        self.assertEqual(opts["tool_choice"], "auto")
        self.assertIs(opts["parallel_tool_calls"], False)
        self.assertEqual(opts["reasoning"], {"effort": "low"})
        self.assertEqual(einstieg._stimme(), {"id": einstieg.STANDARD_STIMME})


if __name__ == "__main__":
    unittest.main()
