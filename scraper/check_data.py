
with open("data/all_banks.txt", "r", encoding="utf-8") as f:
    content = f.read()

banks = ["Ameriabank", "FastBank", "Inecobank"]
topics = ["CREDITS", "DEPOSITS", "BRANCHES"]

for bank in banks:
    print(f"\n── {bank} ──")
    for topic in topics:
        marker = f"[{bank.upper()} — {topic}]"
        if marker in content:
            # find the section and count its characters
            start = content.index(marker)
            end = content.index("\n[", start + 1) if "\n[" in content[start + 1:] else start + 500
            section = content[start:end]
            print(f"  {topic}: {len(section)} characters")
        else:
            print(f"  {topic}: ✗ NOT FOUND")