"""LiveKit entry point for Dinko v2. Configure DINKO_CONTEXT_FILE before starting."""
import json
import logging

from livekit.agents import Agent, AgentServer, AgentSession, ChatContext, JobContext, cli
from livekit.plugins import silero
from livekit.plugins.openai.realtime import GPTLiveModel

from dinko_v2_prompt import new_session
from dinko_v2_runtime import prepare_session

server = AgentServer()
logger = logging.getLogger(__name__)


class Dinko(Agent):
    def __init__(self, config, greeting, *, tools=()):
        context = ChatContext.empty()
        context.add_message(role="user", content=config["input"][1]["content"][0]["text"])
        super().__init__(instructions=config["instructions"], chat_ctx=context, tools=list(tools))
        self.greeting = greeting

    async def on_enter(self):
        handle = self.session.generate_reply(instructions=self.greeting)
        await handle
        if error := handle.exception():
            logger.warning("Dinko greeting failed: %s", type(error).__name__)


def build_session(*, tools=()):
    config, greeting = prepare_session(new_session())
    responses = dict(config["delegation"]["responses"])
    raw_tools = responses.pop("tools")
    if raw_tools:
        raise ValueError("Direkte OpenAI-Bindings brauchen ausführbare LiveKit-Adapter.")
    responses["tool_choice"] = "auto" if tools else "none"
    model = GPTLiveModel(
        model=config["model"],
        voice=config["audio"]["output"]["voice"],
        delegation="responses",
        responses_options=responses,
    )
    return AgentSession(llm=model, vad=silero.VAD.load()), Dinko(
        config, greeting["content"], tools=tools
    )


@server.rtc_session(agent_name="dinko-v2")
async def entrypoint(ctx: JobContext):
    session, agent = build_session()
    await session.start(agent, room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
