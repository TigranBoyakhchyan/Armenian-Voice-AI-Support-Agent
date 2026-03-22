# Armenian Voice AI Support Agent

A real-time voice AI assistant that answers questions about Armenian bank services — credits, deposits, and branch/ATM locations — using the open-source LiveKit framework. The agent understands and speaks Armenian.

---

## Architecture & Design Decisions

### System Overview

```
User (speaks Armenian)
        ↓
LiveKit Server (local, via Docker)
        ↓
STT — OpenAI Whisper (whisper-1)
        ↓
LLM — GPT-4o mini (with full bank data in system prompt)
        ↓
TTS — OpenAI TTS HD (tts-1-hd, nova voice)
        ↓
User (hears Armenian response)
```

### How It Works

1. The user speaks Armenian into their microphone via the LiveKit Playground.
2. LiveKit streams the audio to the agent process running on the local machine.
3. Whisper transcribes the Armenian speech to text.
4. GPT-4o mini reads the question along with the scraped bank data — injected directly into the system prompt — and generates a response in Armenian.
5. OpenAI TTS HD converts the text response to spoken audio.
6. LiveKit delivers the audio back to the user.

### Why These Models

**STT — OpenAI Whisper (`whisper-1`)**
Whisper large-v3 is one of the very few models with reliable Armenian speech recognition. Smaller Whisper variants degrade significantly on Armenian.

**LLM — GPT-4o mini**
The task is straightforward retrieval from a provided context — no complex reasoning needed. GPT-4o mini is fast, cheap, multilingual, and follows instructions reliably. It handles Armenian text well and stays within the token budget.

**TTS — OpenAI TTS HD (`tts-1-hd`, `nova` voice)**
`tts-1-hd` provides higher audio quality than the standard `tts-1` model with only a small latency increase. The `nova` voice handles non-English languages more naturally than other available voices, producing more natural-sounding Armenian output.

### Data Retrieval Strategy

Bank data is scraped from official bank websites and loaded as a single string directly into the LLM system prompt on every request. This approach was chosen because:
- It guarantees maximum context availability — the model always has the full dataset.
- It avoids the complexity of vector databases and embeddings.
- It makes evaluation and quality improvement straightforward — just edit the text files and re-run the scraper.

To prevent the conversation history from growing too large and pushing bank data out of the context window, the agent trims the conversation to the last 4 messages before each LLM call.

### Scalability

Adding a new bank requires only one step — add an entry to `scraper/banks_config.json` with the bank name and relevant page URLs, then re-run the scraper. No code changes are needed anywhere else.

---

## Project Structure

```
armenian-voice-agent/
├── start.py                ← one-click setup and launch script
├── agents/
│   ├── agent.py            ← main voice agent (LiveKit + STT + LLM + TTS)
│   └── test_agent.py       ← text-only LLM test (no voice, no LiveKit)
├── scraper/
│   ├── scraper.py          ← scrapes bank websites using Playwright
│   ├── clean_data.py       ← cleans and balances scraped data
│   ├── check_data.py       ← shows character counts per bank/topic
│   ├── banks_config.json   ← bank names and URLs to scrape
│   └── data/
│       ├── all_banks.txt        ← raw scraped data
│       └── all_banks_clean.txt  ← cleaned data (used by agent)
├── token/
│   └── gen_token.py        ← generates LiveKit room token for testing
├── .env.example            ← template for environment variables
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Prerequisites

Before starting, make sure you have the following installed:

- **Python 3.9+** — download from [python.org](https://python.org)
- **Docker Desktop** — download from [docker.com/products/docker-desktop](https://docker.com/products/docker-desktop), must be running before you start
- **Git** — download from [git-scm.com](https://git-scm.com)

---

## Quick Start (Recommended)

### Step 1 — Clone the repository

```bash
git clone https://github.com/TigranBoyakhchyan/Armenian-Voice-AI-Support-Agent.git
cd Armenian-Voice-AI-Support-Agent
```

### Step 2 — Run the setup script

```bash
python start.py
```

`start.py` handles everything automatically in this order:

1. Checks that Python 3.9+ and Docker are available and running
2. Asks for your LiveKit credentials and OpenAI API key and saves them to `.env`
3. Creates a Python virtual environment
4. Installs all dependencies from `requirements.txt`
5. Installs the Playwright Chromium browser for scraping
6. Starts the LiveKit server via Docker using your credentials
7. Scrapes bank data from all configured banks and cleans it
8. Generates a room token and prints browser connection instructions
9. Launches the voice agent

When `start.py` finishes it will print your room token and exact instructions for connecting.

### Step 3 — Connect and speak

Once `start.py` shows connection instructions:

1. Open [agents-playground.livekit.io](https://agents-playground.livekit.io) in Chrome
2. Set **LiveKit URL** to `ws://localhost:7880`
3. Paste the token from your terminal into the **Token** field
4. Click **Connect** and allow microphone access
5. Speak in Armenian — the agent will respond

---

## Manual Setup (if start.py doesn't work)

Follow these steps if the automatic setup fails for any reason.

### Step 1 — Clone the repository

```bash
git clone https://github.com/TigranBoyakhchyan/Armenian-Voice-AI-Support-Agent.git
cd Armenian-Voice-AI-Support-Agent
```

### Step 2 — Create and activate a virtual environment

**Mac / Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

You should see `(venv)` at the start of your terminal line when it is active. Every command from this point must be run with the venv active.

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

The second command downloads a Chromium browser used for scraping — takes about 1-2 minutes.

### Step 4 — Set up environment variables

Copy the example file:

**Mac / Linux:**
```bash
cp .env.example .env
```

**Windows:**
```powershell
copy .env.example .env
```

Open `.env` in your editor and fill in your values:

```
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=your_chosen_key
LIVEKIT_API_SECRET=your_chosen_secret
OPENAI_API_KEY=sk-your-real-openai-key-here
```

For `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` you can choose any values — for example `devkey` and `secret`. These are just passwords for your local server. The only requirement is that you use the same values when starting Docker in the next step.

### Step 5 — Scrape bank data

```bash
cd scraper
python scraper.py
```

This visits all bank pages listed in `banks_config.json`, extracts text and table data, and automatically runs `clean_data.py` afterwards. Takes 3-5 minutes.

When finished, verify the data was scraped successfully:

```bash
python check_data.py
```

You should see character counts above 1000 for each bank and topic. If any topic shows 0 characters, check that the URL in `banks_config.json` loads correctly in your browser.

### Step 6 — Run the full voice agent

You need **three terminal windows** open at the same time.

**Terminal 1 — Start the LiveKit server**

Replace `your_chosen_key` and `your_chosen_secret` with the exact values from your `.env`:

**Mac / Linux:**
```bash
docker run --rm \
  -p 7880:7880 \
  -p 7881:7881 \
  -p 7882:7882/udp \
  -e LIVEKIT_KEYS="your_chosen_key: your_chosen_secret" \
  livekit/livekit-server \
  --dev
```

**Windows (PowerShell):**
```powershell
docker run --rm -p 7880:7880 -p 7881:7881 -p 7882:7882/udp -e LIVEKIT_KEYS="your_chosen_key: your_chosen_secret" livekit/livekit-server --dev
```

Wait until you see `starting TCP server on :7880`. Leave this terminal open — closing it stops the server.

**Terminal 2 — Start the agent**

Make sure `(venv)` is showing, then:

```bash
cd agents
python agent.py dev
```

Wait until you see `registered worker`. The agent is now running and waiting for someone to join a room.

**Terminal 3 — Generate a room token**

```bash
cd token
python gen_token.py
```

Copy the long token string that is printed.

### Step 7 — Connect via browser

1. Open [agents-playground.livekit.io](https://agents-playground.livekit.io) in Chrome
2. Set **LiveKit URL** to `ws://localhost:7880`
3. Paste the room token into the **Token** field
4. Click **Connect** and allow microphone access
5. Start speaking in Armenian

Watch Terminal 2 for `[STT] Heard:` lines confirming your speech is being transcribed correctly.

---

## Adding a New Bank

Open `scraper/banks_config.json` and add a new entry to the `banks` array:

```json
{
  "name": "New Bank Name",
  "enabled": true,
  "pages": {
    "credits": [
      "https://newbank.am/hy/loans"
    ],
    "deposits": [
      "https://newbank.am/hy/deposits"
    ],
    "branches": [
      "https://newbank.am/hy/branches"
    ]
  }
}
```

Then re-run the scraper:

```bash
cd scraper
python scraper.py
```

No other code changes needed anywhere. To temporarily disable a bank without deleting it, set `"enabled": false`.

---

## Guardrails

The agent is strictly limited to answering questions about:
- Credits and loans
- Deposits
- Branch and ATM locations

It only answers about banks present in the scraped data. For any question outside these three topics it politely refuses in Armenian. It never uses outside knowledge or makes up information — if an answer is not found in the scraped data it says so clearly.

---

## Troubleshooting

**`start.py` crashes at the Docker step**
Make sure Docker Desktop is fully started before running `start.py`. The Docker icon in your taskbar should be stable and not animated. Open Docker Desktop manually and wait for it to finish loading, then run `start.py` again.

**401 Unauthorized error when agent starts**
The LiveKit credentials don't match. The `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` in your `.env` must exactly match the values used when starting the Docker server. Stop the Docker container, check your `.env`, and restart everything. If using `start.py` this is handled automatically.

**Agent says it has no information about a bank**
Run `python scraper/check_data.py`. If any topic shows 0 or very few characters, re-run the scraper. Also open the bank's URL in your browser to confirm it actually loads.

**Branch locations return garbage text or keyboard shortcuts**
The branch page uses an interactive map. Add `"use_map_scraper": true` to that URL entry in `banks_config.json`, or find a PDF link for that bank's branch list and add it instead.

**Rate limit error (429) from OpenAI**
The bank data is too large for the token limit. Open `scraper/clean_data.py`, reduce `MAX_CHARS_PER_TOPIC` from `4000` to `2000`, then run `python scraper/clean_data.py` and restart the agent.

**Agent stops answering correctly after a long conversation**
The conversation history has grown too large and is crowding out the bank data. The agent automatically trims to the last 4 messages to prevent this. If it still happens, reduce `MAX_CHARS_PER_TOPIC` in `clean_data.py` to give more room.

**`ModuleNotFoundError` when running any script**
Your virtual environment is not active. Run `venv\Scripts\Activate.ps1` (Windows) or `source venv/bin/activate` (Mac/Linux) and try again.

**Browser blocks `ws://localhost` connection**
Use Chrome. Go to `chrome://flags/#unsafely-treat-insecure-origin-as-secure`, add `ws://localhost:7880` to the list, enable the flag, and relaunch Chrome. Then try the playground again.

**No audio response from the agent**
Confirm all three components are running — Docker server in Terminal 1, agent in Terminal 2, and that you connected successfully via the playground. Check Terminal 2 for any error messages after you speak.
