def clean_bank_data(input_path="data/all_banks.txt",
                    output_path="data/all_banks.txt"):

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"Before cleaning: {len(content)} characters")

    # split into sections to clean each one separately
    lines = content.split("\n")
    cleaned_lines = []
    seen_lines = set()

    for line in lines:
        stripped = line.strip()

        # always keep section headers
        if stripped.startswith("=") or stripped.startswith("["):
            cleaned_lines.append(line)
            seen_lines = set()  # reset seen lines for each new section
            continue

        # skip empty lines that are duplicated
        if not stripped:
            if cleaned_lines and cleaned_lines[-1].strip():
                cleaned_lines.append("")
            continue

        # skip lines that are just URLs repeated many times
        if stripped.startswith("http") and stripped in seen_lines:
            continue

        # skip very short meaningless lines
        if len(stripped) < 15:
            continue

        # skip duplicate lines within the same section
        if stripped in seen_lines:
            continue

        seen_lines.add(stripped)
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(cleaned)

    print(f"After cleaning:  {len(cleaned)} characters")
    print(f"Reduced by: {len(content) - len(cleaned)} characters "
          f"({100*(len(content)-len(cleaned))//len(content)}%)")

if __name__ == "__main__":
    clean_bank_data()