"""Langfuse-Tracing über OpenTelemetry (übernommen aus dem Lina-Projekt).

Aktiv nur, wenn LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY und LANGFUSE_BASE_URL gesetzt sind.
Ohne Keys läuft Dinko normal weiter.

Datenschutz: Standardmäßig gehen KEINE Gesprächsinhalte an Langfuse: nur Dauer, Modelle,
Tokens, Tool-Namen, Fehler-Typen. Mit LANGFUSE_INHALTE=1 werden auch Transkripte,
Tool-Argumente und Instruktionen übertragen (= Personendaten der Kandidaten).
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Any

from .config import VERSION

logger = logging.getLogger("dinko.telemetrie")


def umgebung() -> str:
    """Langfuse-Environment: DINKO_ENV > LiveKit-Deployment > „production“.

    LIVEKIT_AGENT_DEPLOYMENT ist in der Cloud für production leer.
    """
    env = (
        os.environ.get("DINKO_ENV")
        or os.environ.get("LIVEKIT_AGENT_DEPLOYMENT")
        or "production"
    )
    env = "".join(c if c.isalnum() or c in "-_" else "-" for c in env.lower())[:40]
    return env if env and not env.startswith("langfuse") else "production"


def setup_langfuse(metadata: dict[str, Any] | None = None):
    """Gibt (TracerProvider, DialogProzessor) zurück oder None, wenn Langfuse nicht
    konfiguriert ist."""
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = os.environ.get("LANGFUSE_SECRET_KEY")
    base = os.environ.get("LANGFUSE_BASE_URL")
    if not (pk and sk and base):
        logger.info("Langfuse nicht konfiguriert – Tracing aus")
        return None

    from livekit.agents.telemetry import set_tracer_provider
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    from .dialog import LangfuseDialogProzessor

    auth = base64.b64encode(f"{pk}:{sk}".encode()).decode()
    exporter = OTLPSpanExporter(
        endpoint=f"{base.rstrip('/')}/api/public/otel/v1/traces",
        headers={"Authorization": f"Basic {auth}", "x-langfuse-ingestion-version": "4"},
    )
    inhalte = os.environ.get("LANGFUSE_INHALTE", "0") == "1"
    provider = TracerProvider()
    # Reihenfolge wichtig: der Dialog-Prozessor ergänzt/maskiert im on_end, BEVOR der
    # BatchSpanProcessor exportiert.
    dialog = LangfuseDialogProzessor(inhalte=inhalte)
    provider.add_span_processor(dialog)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    meta: dict[str, Any] = {
        "langfuse.environment": umgebung(),
        "langfuse.release": VERSION,
        "dinko.version": VERSION,
    }
    meta.update(metadata or {})
    set_tracer_provider(provider, metadata=meta, allow_pii=inhalte)
    logger.info(
        "Langfuse-Tracing aktiv (Inhalte: %s, Umgebung: %s, Version: %s)",
        "ja" if inhalte else "nein",
        meta["langfuse.environment"],
        VERSION,
    )
    return provider, dialog
