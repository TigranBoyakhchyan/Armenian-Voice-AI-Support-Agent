import subprocess
import sys
import os
import platform
import time
import shutil
import threading

# detect operating system 
IS_WINDOWS = platform.system() == "Windows"
IS_MAC     = platform.system() == "Darwin"
IS_LINUX   = platform.system() == "Linux"

# paths
ROOT_DIR    = os.path.dirname(os.path.abspath(__file__))
VENV_DIR    = os.path.join(ROOT_DIR, "venv")
SCRAPER_DIR = os.path.join(ROOT_DIR, "scraper")
AGENTS_DIR  = os.path.join(ROOT_DIR, "agents")
TOKEN_DIR   = os.path.join(ROOT_DIR, "token")
ENV_FILE    = os.path.join(ROOT_DIR, ".env")
ENV_EXAMPLE = os.path.join(ROOT_DIR, ".env.example")
CLEAN_DATA  = os.path.join(SCRAPER_DIR, "clean_data.py")
SCRAPER     = os.path.join(SCRAPER_DIR, "scraper.py")
CHECK_DATA  = os.path.join(SCRAPER_DIR, "check_data.py")
AGENT       = os.path.join(AGENTS_DIR, "agent.py")
GEN_TOKEN   = os.path.join(TOKEN_DIR, "gen_token.py")

# Python executable inside venv
if IS_WINDOWS:
    VENV_PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe")
    VENV_PIP    = os.path.join(VENV_DIR, "Scripts", "pip.exe")
else:
    VENV_PYTHON = os.path.join(VENV_DIR, "bin", "python")
    VENV_PIP    = os.path.join(VENV_DIR, "bin", "pip")


# Helpers

def print_step(step: int, total: int, message: str):
    print(f"\n[{step}/{total}] {message}")
    print("─" * 50)


def run(cmd: list, cwd: str = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and print output live."""
    result = subprocess.run(
        cmd,
        cwd=cwd or ROOT_DIR,
        check=check,
    )
    return result


def run_silent(cmd: list, cwd: str = None) -> subprocess.CompletedProcess:
    """Run a command silently, return result without raising on failure."""
    return subprocess.run(
        cmd,
        cwd=cwd or ROOT_DIR,
        capture_output=True,
        text=True,
    )


def ask(question: str) -> str:
    """Ask the user a question and return their answer."""
    return input(f"\n{question}: ").strip()


def confirm(question: str) -> bool:
    """Ask a yes/no question."""
    answer = input(f"\n{question} [y/n]: ").strip().lower()
    return answer in ("y", "yes", "")


# Step checks

def check_python_version():
    """Make sure Python 3.9+ is being used."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"[FAIL] Python 3.9+ required. You have {version.major}.{version.minor}")
        print("       Download from https://python.org")
        sys.exit(1)
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")


def check_docker():
    """Make sure Docker is installed and running."""
    # check if docker is installed
    if shutil.which("docker") is None:
        print("[FAIL] Docker is not installed.")
        print("       Download from https://docker.com/products/docker-desktop")
        sys.exit(1)

    # check if docker daemon is running
    result = run_silent(["docker", "info"])
    if result.returncode != 0:
        print("[FAIL] Docker is installed but not running.")
        print("       Please open Docker Desktop and wait for it to start,")
        print("       then run start.py again.")
        sys.exit(1)

    print("[OK] Docker is running")


def check_env_file():
    """
    Check if .env exists with all required values.
    If anything is missing, guide the user to fill it in.
    """
    # copy from .env.example if .env doesn't exist
    if not os.path.exists(ENV_FILE):
        if os.path.exists(ENV_EXAMPLE):
            shutil.copy(ENV_EXAMPLE, ENV_FILE)
            print("[OK] Created .env from .env.example")
        else:
            with open(ENV_FILE, "w") as f:
                f.write("LIVEKIT_URL=ws://localhost:7880\n")
                f.write("LIVEKIT_API_KEY=\n")
                f.write("LIVEKIT_API_SECRET=\n")
                f.write("OPENAI_API_KEY=\n")
            print("[OK] Created .env file")

    # read current .env
    with open(ENV_FILE, "r") as f:
        content = f.read()

    lines = content.splitlines()
    env_values = {}
    for line in lines:
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            env_values[key.strip()] = value.strip()

    updated = False

    #   check LIVEKIT_API_KEY
    livekit_key = env_values.get("LIVEKIT_API_KEY", "")
    if not livekit_key or livekit_key == "your_livekit_api_key":
        print("\n[!] LIVEKIT_API_KEY is missing.")
        print("    For local development you can use any value e.g. 'devkey'")
        livekit_key = ask("Enter LIVEKIT_API_KEY (press Enter to use 'devkey')")
        if not livekit_key:
            livekit_key = "devkey"
        env_values["LIVEKIT_API_KEY"] = livekit_key
        updated = True
        print(f"[OK] LIVEKIT_API_KEY set to '{livekit_key}'")
    else:
        print(f"[OK] LIVEKIT_API_KEY found: {livekit_key}")

    # check LIVEKIT_API_SECRET 
    livekit_secret = env_values.get("LIVEKIT_API_SECRET", "")
    if not livekit_secret or livekit_secret == "your_livekit_api_secret":
        print("\n[!] LIVEKIT_API_SECRET is missing.")
        print("    For local development you can use any value e.g. 'secret'")
        livekit_secret = ask("Enter LIVEKIT_API_SECRET (press Enter to use 'secret')")
        if not livekit_secret:
            livekit_secret = "secret"
        env_values["LIVEKIT_API_SECRET"] = livekit_secret
        updated = True
        print(f"[OK] LIVEKIT_API_SECRET set to '{livekit_secret}'")
    else:
        print(f"[OK] LIVEKIT_API_SECRET found")

    # ── check LIVEKIT_URL ──
    livekit_url = env_values.get("LIVEKIT_URL", "")
    if not livekit_url:
        env_values["LIVEKIT_URL"] = "ws://localhost:7880"
        updated = True
        print("[OK] LIVEKIT_URL set to 'ws://localhost:7880'")
    else:
        print(f"[OK] LIVEKIT_URL found: {livekit_url}")

    # ── check OPENAI_API_KEY ──
    openai_key = env_values.get("OPENAI_API_KEY", "")
    if not openai_key or openai_key == "your_openai_api_key_here":
        openai_key = ask("Paste your OpenAI API key here (starts with sk-)")
        if not openai_key.startswith("sk-"):
            print("[WARN] That doesn't look like a valid OpenAI key (should start with sk-)")
            if not confirm("Continue anyway?"):
                sys.exit(1)
        env_values["OPENAI_API_KEY"] = openai_key
        updated = True
        print("[OK] OpenAI API key saved")
    else:
        print("[OK] OpenAI API key found")

    # ── write updated .env if anything changed ──
    if updated:
        with open(ENV_FILE, "w") as f:
            # preserve existing keys order and write all values
            written_keys = set()
            new_lines = []
            for line in lines:
                if "=" in line and not line.startswith("#"):
                    key = line.split("=", 1)[0].strip()
                    if key in env_values:
                        new_lines.append(f"{key}={env_values[key]}")
                        written_keys.add(key)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)

            # add any new keys that weren't in the original file
            for key, value in env_values.items():
                if key not in written_keys:
                    new_lines.append(f"{key}={value}")

            f.write("\n".join(new_lines) + "\n")

        print("\n[OK] .env file updated")


# Setup steps

def setup_venv():
    """Create virtual environment if it doesn't exist."""
    if os.path.exists(VENV_PYTHON):
        print("[OK] Virtual environment already exists")
        return

    print("Creating virtual environment...")
    run([sys.executable, "-m", "venv", "venv"])
    print("[OK] Virtual environment created")


def install_dependencies():
    """Install all Python packages from requirements.txt."""
    req_file = os.path.join(ROOT_DIR, "requirements.txt")
    if not os.path.exists(req_file):
        print("[FAIL] requirements.txt not found")
        sys.exit(1)

    print("Installing Python packages (this may take a minute)...")
    run([VENV_PIP, "install", "-r", req_file, "--quiet"])
    print("[OK] Python packages installed")


def install_playwright():
    """Install Playwright Chromium browser for scraping."""
    print("Installing Playwright Chromium browser...")
    run([VENV_PYTHON, "-m", "playwright", "install", "chromium"])
    print("[OK] Playwright Chromium installed")


def start_livekit_server():
    """Start LiveKit server in Docker as a background process."""

    # read keys from .env to ensure they match what the agent uses
    api_key = "devkey"
    api_secret = "secret"

    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("LIVEKIT_API_KEY="):
                    val = line.split("=", 1)[1].strip()
                    if val:
                        api_key = val
                elif line.startswith("LIVEKIT_API_SECRET="):
                    val = line.split("=", 1)[1].strip()
                    if val:
                        api_secret = val

    print(f"Using LiveKit credentials — key: {api_key}")

    # check if already running
    result = run_silent(["docker", "ps", "--filter",
                         "ancestor=livekit/livekit-server",
                         "--format", "{{.ID}}"])
    if result.stdout.strip():
        print("[OK] LiveKit server is already running")
        return None

    print("Starting LiveKit server in Docker...")

    cmd = [
        "docker", "run", "--rm",
        "-p", "7880:7880",
        "-p", "7881:7881",
        "-p", "7882:7882/udp",
        "-e", f"LIVEKIT_KEYS={api_key}: {api_secret}",
        "livekit/livekit-server",
        "--dev"
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # wait for server to be ready
    print("Waiting for LiveKit server to start", end="", flush=True)
    for _ in range(30):
        time.sleep(1)
        print(".", end="", flush=True)
        result = run_silent(["docker", "ps", "--filter",
                             "ancestor=livekit/livekit-server",
                             "--format", "{{.ID}}"])
        if result.stdout.strip():
            print()
            print("[OK] LiveKit server is running on port 7880")
            return process

    print()
    print("[FAIL] LiveKit server did not start in time")
    print("Check that ports 7880, 7881, 7882 are not in use")
    sys.exit(1)


def run_scraper():
    """Scrape bank data and clean it."""
    clean_file = os.path.join(SCRAPER_DIR, "data", "all_banks_clean.txt")

    # ask if user wants to re-scrape if data already exists
    if os.path.exists(clean_file):
        print("[OK] Bank data already exists")
        if not confirm("Re-scrape bank data? (takes 3-5 minutes, say n to use existing data)"):
            print("[OK] Using existing bank data")
            return

    print("Scraping bank websites (this takes 3-5 minutes)...")
    print("You will see live output as each page is fetched.\n")
    run([VENV_PYTHON, "scraper.py"], cwd=SCRAPER_DIR)
    print("\n[OK] Bank data scraped and cleaned")


def verify_data():
    """Show data summary to confirm scraping worked."""
    print("Verifying scraped data...")
    run([VENV_PYTHON, "check_data.py"], cwd=SCRAPER_DIR)


def generate_token() -> str:
    """Generate and return a LiveKit room token."""
    result = run_silent([VENV_PYTHON, "gen_token.py"], cwd=TOKEN_DIR)
    if result.returncode != 0:
        print(f"[FAIL] Token generation failed: {result.stderr}")
        sys.exit(1)
    token = result.stdout.strip()
    return token


def print_connection_instructions(token: str):
    """Print instructions for connecting via the browser."""
    print("\n" + "=" * 60)
    print("AGENT IS RUNNING — CONNECT VIA BROWSER")
    print("=" * 60)
    print()
    print("1. Open this URL in your browser:")
    print("   https://agents-playground.livekit.io")
    print()
    print("2. Fill in the connection details:")
    print("   LiveKit URL : ws://localhost:7880")
    print("   Token       : (see below)")
    print()
    print("3. Paste this token into the Token field:")
    print()
    print(f"   {token}")
    print()
    print("4. Click Connect and allow microphone access")
    print()
    print("5. Speak in Armenian and the agent will respond")
    print()
    print("─" * 60)
    print()
    print("Press Ctrl+C to stop the agent")
    print("=" * 60)
    input(
        "\n" +
        "=" * 60 + "\n"
        "ATTENTION: Do NOT press Connect yet!\n"
        "The LiveKit server is still starting up.\n"
        "Wait until you see '[OK] LiveKit server is running on port 7880'\n"
        "in the terminal above, THEN open the playground and connect.\n\n"
        "If you already pressed Connect and got an error, just\n"
        "refresh the playground page and try again.\n"
        "(Maybe a couple of times. Personal experience =) )\n" +
        "=" * 60 + "\n\n"
        "Press Enter when you are ready to continue..."
    )


def run_agent():
    """Run the voice agent (blocking — runs until Ctrl+C)."""
    print("Starting voice agent...")
    run([VENV_PYTHON, "agent.py", "dev"], cwd=AGENTS_DIR)


def main():
    TOTAL_STEPS = 8

    print("=" * 60)
    print("Armenian Voice AI Support Agent — Setup & Launch")
    print("=" * 60)

    # Step 1: Check prerequisites
    print_step(1, TOTAL_STEPS, "Checking prerequisites")
    check_python_version()
    check_docker()

    # Step 2: Check/create .env with API key
    print_step(2, TOTAL_STEPS, "Setting up environment variables")
    check_env_file()

    # Step 3: Create virtual environment ──
    print_step(3, TOTAL_STEPS, "Setting up virtual environment")
    setup_venv()

    # Step 4: Install dependencies
    print_step(4, TOTAL_STEPS, "Installing dependencies")
    install_dependencies()
    install_playwright()

    # Step 5: Start LiveKit server
    print_step(5, TOTAL_STEPS, "Starting LiveKit server")
    livekit_process = start_livekit_server()

    # Step 6: Scrape bank data
    print_step(6, TOTAL_STEPS, "Scraping bank data")
    run_scraper()

    # Step 7: Verify data 
    print_step(7, TOTAL_STEPS, "Verifying scraped data")
    verify_data()

    # Step 8: Generate token and launch agent ──
    print_step(8, TOTAL_STEPS, "Launching voice agent")
    token = generate_token()
    print_connection_instructions(token)

    # run agent (blocking until Ctrl+C)
    try:
        run_agent()
    except KeyboardInterrupt:
        print("\n\nStopping agent...")

    # cleanup — stop LiveKit server if we started it
    if livekit_process:
        print("Stopping LiveKit server...")
        livekit_process.terminate()
        print("[OK] LiveKit server stopped")

    print("\nGoodbye!")


if __name__ == "__main__":
    main()
