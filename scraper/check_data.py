import json

with open("data/all_banks.txt", "r", encoding="utf-8") as f:
    content = f.read()

def load_banks(config_path: str = "banks_config.json") -> list:
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    banks = [b for b in config["banks"] if b.get("enabled", True)]
    bank_names = [d['name'] for d in banks]
    print(f"Loaded {len(banks)} enabled banks from {config_path}")
    return bank_names

banks = load_banks()
topics = ["CREDITS", "DEPOSITS", "BRANCHES"]

for bank in banks:
    print(f"\n--- {bank} ---")
    for topic in topics:
        marker = f"[{bank.upper()} — {topic}]"
        if marker in content:
            # find the section and count its characters
            start = content.index(marker)
            end = content.index("\n[", start + 1) if "\n[" in content[start + 1:] else start + 500
            section = content[start:end]
            print(f"  {topic}: {len(section)} characters")
        else:
            print(f"  {topic}: NOT FOUND")