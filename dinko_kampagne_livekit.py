#!/usr/bin/env python3
"""Einstieg: Dinko-Kampagne (ausgehender Kurzanruf, Casting Bihać 18.11.2026).

Ablauf: Kandidat aus den Dispatch-Metadaten `{"record_id": "rec..."}` → Daten aus Airtable
(vor dem Sessionstart) → GPT-Live-Session → warten, bis sich jemand meldet
(Anrufbeantworter-Erkennung) → Gespräch → Ergebnis, Status und Transkript speichern →
Raum löschen (= auflegen).

Gewählt wird nicht hier: Den Anruf startet der Wählautomat (n8n) über LiveKit, wie bei Lina.
Nur zum lokalen Testen ohne Metadaten gilt DINKO_TEST_RECORD_ID.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

from livekit.agents import (
    AMD,
    AgentServer,
    AgentSession,
    CloseEvent,
    ConversationItemAddedEvent,
    JobContext,
    cli,
    room_io,
)
from livekit.agents.beta import EndCallTool
from livekit.plugins import silero
from livekit.plugins.openai.realtime import GPTLiveModel

try:  # Standard-Prompt der Anrufbeantworter-Erkennung; ohne ihn bleibt der Standard aktiv.
    from livekit.agents.voice.amd.classifier import AMD_PROMPT
except ImportError:
    AMD_PROMPT = None

# Plugins müssen beim Start im Hauptthread geladen werden, nicht erst im Anruf.
try:
    from livekit.plugins import ai_coustics
except ImportError:  # ohne das Paket läuft Dinko ohne Rauschunterdrückung
    ai_coustics = None

from dinko_kampagne import prompts, r2, zeit
from dinko_kampagne.agent import DinkoKampagne
from dinko_kampagne.airtable import AirtableStore, gueltige_record_id
from dinko_kampagne.config import AGENT_NAME, CAMPAIGN_ID, VERSION, F
from dinko_kampagne.dialog import DialogProtokoll
from dinko_kampagne.ishod import Stanje, zavrsna_polja
from dinko_kampagne.telemetrie import setup_langfuse, umgebung
from dinko_kampagne.tisina import Tisina

logger = logging.getLogger("dinko.kampagne")

STANDARD_STIMME = "voice_6af797951df481919699d7e887688698"
# AMD-Gründe, bei denen kein Mensch in der Leitung ist (livekit-agents 1.8: AMD settelt
# „uncertain“ mit diesen reasons, wenn der Anruf vor dem Audio endet oder der Angerufene
# während der Erkennung auflegt).
LEERER_ANRUF = frozenset({"participant_missing", "participant_disconnected"})


def _record_id(ctx: JobContext) -> str | None:
    meta = (ctx.job.metadata or "").strip()
    if meta:
        try:
            rid = str(json.loads(meta).get("record_id") or "")
        except (ValueError, AttributeError):
            rid = ""
    else:
        rid = os.getenv("DINKO_TEST_RECORD_ID", "")
    if gueltige_record_id(rid):
        return rid
    logger.error("Kein gültiges record_id in den Dispatch-Metadaten")
    return None


def _sekunden(name: str, standard: float) -> float:
    try:
        return float(os.getenv(name, str(standard)))
    except ValueError:
        return standard


def _amd_optionen() -> dict:
    """Erkennung mit bosnischen Beispielen. DINKO_AMD_PROMPT=0 nimmt den LiveKit-Standard."""
    if AMD_PROMPT is None or os.getenv("DINKO_AMD_PROMPT", "1") != "1":
        return {}
    return {"prompt": AMD_PROMPT + "\n\n" + prompts.AMD_DODATAK}


def _stimme() -> str | dict[str, str]:
    v = os.getenv("DINKO_VOICE_ID", STANDARD_STIMME).strip() or STANDARD_STIMME
    return {"id": v} if v.startswith("voice_") else v


def _responses_options(ctx_daten: dict) -> dict:
    """Backend-Modell hinter GPT-Live. Leere Umgebungsvariable = Option weglassen."""
    opts: dict = {
        "model": os.getenv("DINKO_BACKEND_MODEL", "gpt-5.6-sol"),
        "instructions": prompts.backend_instructions(ctx_daten),
        "parallel_tool_calls": False,
        "tool_choice": "auto",
    }
    if effort := os.getenv("DINKO_BACKEND_REASONING", "low").strip():
        opts["reasoning"] = {"effort": effort}
    return opts


def _tekst_iz_historije(history) -> str:
    linije = []
    for item in getattr(history, "items", None) or []:
        role = getattr(item, "role", None)
        if role not in ("user", "assistant"):
            continue
        tekst = (getattr(item, "text_content", None) or "").strip()
        if tekst:
            linije.append(("Kandidat: " if role == "user" else "Dinko: ") + tekst)
    return "\n".join(linije)


def _room_options() -> room_io.RoomOptions:
    """Rauschunterdrückung wie bei Lina (GSM-Leitung). Aus mit DINKO_NOISE_CANCELLATION=0."""
    if os.getenv("DINKO_NOISE_CANCELLATION", "1") != "1":
        return room_io.RoomOptions()
    if ai_coustics is None:
        logger.warning("ai_coustics nicht installiert – ohne Rauschunterdrückung")
        return room_io.RoomOptions()
    try:
        return room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=ai_coustics.audio_enhancement(
                    model=ai_coustics.EnhancerModel.QUAIL_VF_S
                ),
            ),
        )
    except Exception:
        logger.exception("Rauschunterdrückung nicht verfügbar – ohne weiter")
        return room_io.RoomOptions()


async def _auflegen(ctx: JobContext) -> None:
    """Raum löschen: trennt auch den SIP-Teilnehmer, die Leitung wird frei."""
    try:
        await ctx.delete_room()
    except Exception:
        logger.info("Raum war schon geschlossen")


server = AgentServer()


@server.rtc_session(agent_name=AGENT_NAME)
async def entrypoint(ctx: JobContext) -> None:
    record_id = _record_id(ctx)
    if not record_id:
        await _auflegen(ctx)
        ctx.shutdown(reason="no record_id")
        return
    ctx.log_context_fields = {"room": ctx.room.name, "record_id": record_id}

    # Langfuse (optional): vor dem Sessionstart, damit alle Spans ankommen.
    langfuse = setup_langfuse(
        metadata={
            "langfuse.session.id": ctx.room.name,
            "dinko.record_id": record_id,
            "dinko.kampanja": CAMPAIGN_ID,
        }
    )
    trace_provider, dialog_prozessor = langfuse if langfuse else (None, None)
    if trace_provider is not None:

        async def flush_trace() -> None:
            trace_provider.force_flush()

        ctx.add_shutdown_callback(flush_trace)

    # Daten VOR dem Sessionstart holen. Ohne Kontext wird nicht gesprochen.
    store = AirtableStore()
    try:
        polja = await store.ucitaj(record_id)
    except Exception:
        logger.exception("Daten aus Airtable nicht geladen")
        await _auflegen(ctx)
        ctx.shutdown(reason="pre-call fetch failed")
        return
    if polja.get(F.DNC):
        logger.warning("Anrufverbot gesetzt – kein Gespräch")
        await _auflegen(ctx)
        ctx.shutdown(reason="do not call")
        return

    stanje = Stanje(record_id=record_id)
    ctx_daten = prompts.kontekst(polja, zeit.sada())

    tisina_s = _sekunden("DINKO_SILENCE_S", 7.0)
    session = AgentSession(
        llm=GPTLiveModel(
            model=os.getenv("DINKO_VOICE_MODEL", "gpt-live-1"),
            voice=_stimme(),
            delegation="responses",
            responses_options=_responses_options(ctx_daten),
        ),
        # GPT-Live steuert Turns selbst; die VAD ist nötig, damit Unterbrechen die
        # Wiedergabe stoppt.
        vad=silero.VAD.load(),
        userdata=stanje,
        # Stille auf beiden Seiten: nach so vielen Sekunden fragt Dinko einmal nach.
        user_away_timeout=tisina_s if tisina_s > 0 else None,
    )

    async def _nachfragen() -> None:
        handle = session.generate_reply(instructions=prompts.PROVJERA_TISINE)
        await handle.wait_for_playout()

    tisina = Tisina(
        nachfragen=_nachfragen,
        auflegen=lambda grund: ctx.shutdown(reason=grund),
        nach_s=_sekunden("DINKO_SILENCE_HANGUP_S", 8.0),
        gespraech_fertig=stanje.zavrsen,
    )

    @session.on("user_state_changed")
    def _stanje_kandidata(ev) -> None:
        tisina.user_state(str(getattr(ev, "new_state", "")))

    protokoll = DialogProtokoll()
    if dialog_prozessor is not None:
        dialog_prozessor.binde(
            protokoll, {"record_id": record_id, "umgebung": umgebung(), "version": VERSION}
        )

    @session.on("conversation_item_added")
    def _item(ev: ConversationItemAddedEvent) -> None:
        protokoll.dodaj(ev.item)
        role = getattr(ev.item, "role", None)
        if role == "user" and (getattr(ev.item, "text_content", None) or "").strip():
            stanje.kandidat_govorio = True
        elif role == "assistant":
            stanje.dinko_govorio = True

    @session.on("speech_created")
    def _govor(_ev) -> None:
        stanje.dinko_govorio = True

    @session.on("agent_state_changed")
    def _stanje_agenta(ev) -> None:
        if getattr(ev, "new_state", "") == "speaking":
            stanje.dinko_govorio = True

    @session.on("user_input_transcribed")
    def _kandidat(ev) -> None:
        if (getattr(ev, "transcript", "") or "").strip():
            stanje.kandidat_govorio = True

    @session.on("close")
    def _kraj(ev: CloseEvent) -> None:
        protokoll.abschluss = {
            "ishod": stanje.ishod,
            "amd": stanje.amd,
            "razlog_kraja": str(getattr(ev, "reason", "") or ""),
        }
        protokoll.beendet = True

    async def spremi_na_kraju() -> None:
        """Status, Ergebnis und Transkript speichern, dann den Raum löschen (auflegen)."""
        if not stanje.sacuvano:
            stanje.sacuvano = True
            link = None
            try:
                transkript = _tekst_iz_historije(session.history)
                if transkript:
                    key = f"dinko/{umgebung()}/{record_id}/{zeit.sada():%Y%m%dT%H%M%S}.txt"
                    link = await r2.stavi(key, transkript)
            except Exception:
                logger.exception("Transkript nicht gespeichert")
            try:
                await store.azuriraj(record_id, zavrsna_polja(stanje, link))
            except Exception:
                logger.exception("Abschluss nicht in Airtable gespeichert")
        await _auflegen(ctx)

    ctx.add_shutdown_callback(spremi_na_kraju)

    agent = DinkoKampagne(
        instructions=prompts.voice_instructions(ctx_daten),
        stanje=stanje,
        store=store,
        tools=[EndCallTool(end_instructions=None, ignore_on_enter=True)],
    )
    await session.start(agent=agent, room=ctx.room, room_options=_room_options())
    await ctx.connect()

    # Harte Obergrenze: kein Anruf belegt die Leitung länger als DINKO_MAX_CALL_S.
    max_s = _sekunden("DINKO_MAX_CALL_S", 480.0)
    if max_s > 0:

        async def _obergrenze() -> None:
            await asyncio.sleep(max_s)
            logger.warning("Obergrenze von %.0f s erreicht – auflegen", max_s)
            ctx.shutdown(reason="max duration")

        obergrenze = asyncio.create_task(_obergrenze())

        async def _obergrenze_beenden() -> None:
            obergrenze.cancel()

        ctx.add_shutdown_callback(_obergrenze_beenden)

    # Nicht sofort reden: warten, bis sich die angerufene Person meldet.
    try:
        async with AMD(
            session,
            # Der Standard-STT von AMD ist in der EU-Region nicht verfügbar (Erfahrung aus
            # dem Lina-Projekt); Nova-3 hat einen EU-Endpunkt und Bosnisch.
            stt=os.getenv("DINKO_AMD_STT", "deepgram/nova-3:bs"),
            ivr_detection=False,
            **({"detection_options": amd_optionen} if (amd_optionen := _amd_optionen()) else {}),
        ) as detector:
            amd = await detector.execute()
        stanje.amd = str(getattr(amd.category, "value", amd.category))
        amd_grund = str(getattr(amd, "reason", "") or "")
        logger.info("AMD category=%s reason=%s", stanje.amd, amd_grund)
    except Exception:
        logger.exception("AMD fehlgeschlagen – weiter wie Mensch")
        stanje.amd = "fehler"
        amd_grund = ""

    # Niemand in der Leitung (nicht abgenommen, besetzt, aufgelegt): sofort beenden statt
    # 4 s zu warten und in einen leeren Raum zu sprechen. Am 16.11. betraf das 160 von 273
    # Anrufen; die Begrüßung ins Leere erzeugte „did not start speaking“-Fehler.
    if stanje.amd == "uncertain" and amd_grund in LEERER_ANRUF:
        logger.info("Niemand in der Leitung (%s) – auflegen", amd_grund)
        ctx.shutdown(reason=f"no participant: {amd_grund}")
        return

    if stanje.amd == "machine-vm":
        try:
            handle = session.generate_reply(instructions=prompts.GOVORNA_POSTA)
            await handle.wait_for_playout()
        except Exception:
            logger.exception("Nachricht auf der Mailbox fehlgeschlagen")
        ctx.shutdown(reason="voicemail")
        return
    if stanje.amd == "machine-unavailable":
        ctx.shutdown(reason="mailbox unavailable")
        return

    # Ab jetzt gilt die Stille-Behandlung. War es während der Erkennung schon still, steht
    # der Zustand auf „away“ und der Zähler muss neu anlaufen.
    tisina.aktiviere()
    try:
        session.reset_away_timer()
    except Exception:
        logger.exception("Stille-Zähler nicht neu gestartet")

    # Sicherheitsnetz: Meldet sich ein Mensch und Dinko bleibt still, begrüßt der Code.
    try:
        warten = float(os.getenv("DINKO_GREETING_FALLBACK_S", "4"))
    except ValueError:
        warten = 4.0
    if warten > 0:
        await asyncio.sleep(warten)
        if not stanje.dinko_govorio:
            logger.info("Dinko war still – Begrüßung durch den Code")
            try:
                session.generate_reply(instructions=prompts.POZDRAV_REZERVA)
            except Exception:
                logger.exception("Begrüßung durch den Code fehlgeschlagen")


if __name__ == "__main__":
    cli.run_app(server)
