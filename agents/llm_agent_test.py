import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def load_bank_data(path: str = "../scraper/data/all_banks.txt") -> str:
    """Load the scraped bank data from disk."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Bank data not found at '{path}'. "
            f"Run scraper.py first."
        )
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()
    print(f"✓ Loaded bank data: {len(data)} characters")
    return data


def build_system_prompt(bank_data: str) -> str:
    """
    Build the system prompt that:
    1. Loads the full bank data
    2. Instructs the model to answer ONLY from that data
    3. Instructs it to respond in Armenian
    4. Instructs it to refuse off-topic questions
    """
    return f"""Դու հայկական բանկային աջակցության օգնական ես։
Քո անունը «Բանկային Օգնական» է։

ԿԱՐԵՎՈՐ ԿԱՆՈՆՆԵՐ.
1. Պատասխանիր ՄԻԱՅՆ հայերեն լեզվով։
2. Պատասխանիր ՄԻԱՅՆ հետևյալ երեք թեմաների վերաբերյալ.
   - Վարկեր (credits/loans)
   - Ավանդներ (deposits)
   - Մասնաճյուղեր և բանկոմատներ (branches and ATMs)
3. Օգտագործիր ՄԻԱՅՆ ստորև տրված բանկային տվյալները։ Մի օգտագործիր արտաքին գիտելիքներ։
4. Եթե հարցը վերաբերում է այլ թեմայի, քաղաքավարի կերպով մերժիր և բացատրիր, որ կարող ես օգնել միայն վարկերի, ավանդների և մասնաճյուղերի հարցերով։
5. Եթե տվյալները չեն պարունակում պատասխան, ասա որ տեղեկությունը հասանելի չէ։

ԲԱՆԿԱՅԻՆ ՏՎՅԱԼՆԵՐ.
{bank_data}
"""


def ask(system_prompt: str, question: str) -> str:
    """Send a question to GPT-4o mini and return the response."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": question},
        ],
        temperature=0.3,  # lower = more consistent, factual answers
        max_tokens=500,
    )
    return response.choices[0].message.content


def run_tests(system_prompt: str):
    """
    Run a set of test questions to verify the agent works correctly.
    Tests both valid questions and off-topic ones (guardrail check).
    """
    test_questions = [
        # ── valid questions (should be answered) ──
        "Ի՞նչ վարկեր է առաջարկում Ամերիաբանկը:",
        "Արդշինբանկի ավանդների տոկոսադրույքները որո՞նք են:",
        "Ֆաստ Բանկի մասնաճյուղերը որտե՞ղ են գտնվում:",
        "Ինեկոբանկում ի՞նչ պայմաններ կան սպառողական վարկի համար:",

        # ── off-topic questions (should be refused) ──
        "Ո՞րն է Հայաստանի մայրաքաղաքը:",
        "Ե՞րբ է հիմնադրվել Ամերիաբանկը:",
        "Ի՞նչ եղանակ է այսօր Երևանում:",
    ]

    print("\n" + "="*60)
    print("RUNNING AGENT TESTS")
    print("="*60)

    for i, question in enumerate(test_questions, 1):
        print(f"\n[Test {i}] Question: {question}")
        print("-" * 40)
        answer = ask(system_prompt, question)
        print(f"Answer: {answer}")
        print("-" * 40)


def interactive_mode(system_prompt: str):
    """
    Interactive chat mode — type your own questions.
    Type 'quit' to exit.
    """
    print("\n" + "="*60)
    print("INTERACTIVE MODE — type your questions in Armenian or English")
    print("Type 'quit' to exit")
    print("="*60)

    while True:
        question = input("\nYou: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            print("Exiting.")
            break
        if not question:
            continue
        answer = ask(system_prompt, question)
        print(f"\nAgent: {answer}")


if __name__ == "__main__":
    # 1. load the scraped bank data
    bank_data = load_bank_data()

    # 2. build the system prompt with bank data injected
    system_prompt = build_system_prompt(bank_data)

    print(f"✓ System prompt ready: {len(system_prompt)} characters total")

    # 3. run automated tests first
    run_tests(system_prompt)

    # 4. then switch to interactive mode so you can test manually
    interactive_mode(system_prompt)