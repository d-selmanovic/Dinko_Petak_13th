# Dinko-Kampagne für LiveKit Cloud. Enthält nur den Kampagnencode, keine Kandidatendaten.
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim-bookworm AS base
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/.cache/huggingface
ENV TORCH_HOME=/app/.cache/torch

FROM base AS build
RUN apt-get update && apt-get install -y gcc g++ python3-dev \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY requirements-livekit.txt requirements-kampagne.txt ./
RUN pip install --no-cache-dir -r requirements-kampagne.txt
COPY dinko_kampagne ./dinko_kampagne
COPY dinko_kampagne_livekit.py ./
# Modelldateien (Silero VAD) vorab laden, damit der Start nicht darauf wartet.
RUN python dinko_kampagne_livekit.py download-files

FROM base
ARG UID=10001
RUN adduser --disabled-password --gecos "" --home "/app" --shell "/sbin/nologin" \
    --uid "${UID}" appuser
COPY --from=build --chown=appuser:appuser /app /app
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
USER appuser
CMD ["python", "dinko_kampagne_livekit.py", "start"]
