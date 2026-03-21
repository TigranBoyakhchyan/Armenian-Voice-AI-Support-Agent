import asyncio
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent
from livekit.plugins import openai, silero

load_dotenv()

class BankAssistant(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a helpful Armenian bank assistant. Respond only in Armenian."
        )

    async def on_enter(self):
        await self.session.generate_reply(
            instructions="Greet the user in Armenian and ask how you can help."
        )

async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=openai.STT(language="hy"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(voice="nova"),
    )

    await session.start(
        room=ctx.room,
        agent=BankAssistant(),
    )

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))