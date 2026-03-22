import asyncio
import logging
import os
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent
from livekit.plugins import openai, silero
from livekit.agents import llm

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_bank_data(path: str = "../scraper/data/all_banks.txt",
                   max_chars: int = 80000) -> str:
    
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Bank data not found at '{path}'. "
            f"Run crawler.py first."
        )
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()

    if len(data) > max_chars:
        logger.warning(
            f"Bank data truncated from {len(data)} "
            f"to {max_chars} characters to fit token limit"
        )
        data = data[:max_chars]

    logger.info(f"Loaded bank data: {len(data)} characters")
    return data

def build_system_prompt(bank_data: str) -> str:
    return f"""You are a voice-based Armenian bank support assistant.
Your name is "Բանկային Օգնական" (Bank Assistant).

LANGUAGE RULES:
- Always respond in Armenian language only. ALWAYS IN ARMENIAN AND NO OTHER LANGUAGE.
- Never respond in English or Russian, even if the user speaks to you in those languages.
- If the user speaks in English or Russian, politely ask them to speak in Armenian.

TOPIC RULES:
- Only answer questions about these 3 topics:
  1. Credits and loans
  2. Deposits
  3. Branch and ATM locations
- Answer questions only about the banks mentioned in the bank data below. But
  answer to the questions about all of the banks, not only one or two of them, about all of the 
  banks mentioned in the bank data. 
- If the user asks about a bank not present in the bank data, say you do not have
  information about that bank, but if the bank is present, than answer the question.
- If the user asks about anything outside these 3 topics, politely refuse in Armenian
  and explain that you can only help with credits, deposits, and branch locations.

DATA RULES:
- Use ONLY the bank data provided below to answer questions.
- Analyze the data thoroughly and don't say you don't have information if you have the information given.
- Do not use any outside knowledge or make up information.
- If the answer is not found in the data below, say the information is not available.

NUMBER FORMATTING RULES (very important for voice):
- Always write all numbers in Armenian words, never use digits.
- Examples:
  - 5,000,000 → հինգ միլիոն
  - 14% → տասնչորս տոկոս
  - 12 months → տասներկու ամիս
  - 2 years → երկու տարի
  - 0.1% → զրո ամբողջ մեկ տոկոս

RESPONSE FORMAT RULES (very important for voice):
- Keep all responses short — maximum 3 to 4 sentences.
- Never use bullet points, numbered lists, or special characters.
- Speak in natural conversational sentences only.
- Do not use symbols like %, $, AMD — spell them out in Armenian words instead.
  Examples: տոկոս (percent), դոլար (dollar), դրամ (dram)

BANK DATA:
{bank_data}
"""


class BankAssistant(Agent):
    def __init__(self, system_prompt: str):
        super().__init__(instructions=system_prompt)

    async def on_enter(self):
        await self.session.generate_reply(
            instructions=(
                "Բարևիր օգտատիրոջը հայերեն և հարցրու "
                "թե ինչով կարող ես օգնել վարկերի, "
                "ավանդների կամ մասնաճյուղերի վերաբերյալ։"
            )
        )

    async def on_user_turn_completed(
        self,
        turn_ctx: llm.ChatContext,
        new_message: llm.ChatMessage
    ) -> None:
        """
        Trim conversation history before each LLM call to prevent
        bank data from being pushed out of the context window.
        """
        MAX_TURNS = 4  # keep last 4 messages (2 exchanges)

        # get a copy of the current context to modify
        chat_ctx = self.chat_ctx.copy()

        # filter only ChatMessage items (skip FunctionCall etc.)
        messages = [
            item for item in chat_ctx.items
            if isinstance(item, llm.ChatMessage)
        ]

        # separate system messages from conversation
        system_messages = [m for m in messages if m.role == "system"]
        conversation    = [m for m in messages if m.role != "system"]

        # trim conversation to last MAX_TURNS
        if len(conversation) > MAX_TURNS:
            trimmed = system_messages + conversation[-MAX_TURNS:]
            # rebuild context with only trimmed messages
            trimmed_ctx = llm.ChatContext(trimmed)
            await self.update_chat_ctx(trimmed_ctx)


async def entrypoint(ctx: agents.JobContext):
    # 1. load bank data before connecting to the room
    bank_data = load_bank_data()
    system_prompt = build_system_prompt(bank_data)

    # 2. connect to the LiveKit room
    await ctx.connect()
    logger.info(f"Connected to room: {ctx.room.name}")

    # 3. build the full STT → LLM → TTS pipeline
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=openai.STT(model="whisper-1", language="hy"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(model="tts-1-hd", voice="nova"),
    )

    # 4. log every transcription so you can monitor in terminal
    @session.on("user_input_transcribed")
    def on_transcribed(event):
        logger.info(f"[STT] Heard: {event.transcript}")

    # 5. start the agent in the room with the full bank prompt
    await session.start(
        room=ctx.room,
        agent=BankAssistant(system_prompt=system_prompt),
    )

if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)
    )