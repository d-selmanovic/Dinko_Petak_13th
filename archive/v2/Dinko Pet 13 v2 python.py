#!/usr/bin/env python3
"""Dinko V2. DINKO_CONTEXT_FILE required. DINKO_DRY_RUN=1 validates offline."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from dinko_v2_prompt import new_session

session = new_session()
from dinko_v2_runtime import prepare_session, output_payload

session, greeting_event = prepare_session(session)
if os.environ.get("DINKO_DRY_RUN") == "1":
    print(json.dumps(output_payload(session, greeting_event), ensure_ascii=False, indent=2))
else:
    key = os.environ["OPENAI_API_KEY"]
    sdp = Path(os.environ.get("DINKO_OFFER_FILE", "offer.sdp")).read_text(encoding="utf-8")
    payload = {"session": session, "transport": {"type": "webrtc", "sdp": sdp}}
    request = Request("https://api.openai.com/v1/live/sessions", data=json.dumps(payload).encode("utf-8"),
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=60) as response:
        result = json.load(response)
    answer_sdp = result["transport"]["sdp"]
    result["dinko_greeting_event"] = greeting_event
    print(json.dumps(result, ensure_ascii=False))
# Client: apply transport.sdp, then send dinko_greeting_event once after session.started.
# Keep microphone input active and verify output audio. Handle tool events in the application.
