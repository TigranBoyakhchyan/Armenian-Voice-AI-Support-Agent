import asyncio
import os
import json
from playwright.async_api import async_playwright


def load_config(config_path: str = "banks_config.json") -> list:
    """Load bank config from JSON file. Returns only enabled banks."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    banks = [b for b in config["banks"] if b.get("enabled", True)]
    print(f"Loaded {len(banks)} enabled banks from {config_path}")
    return banks


async def scrape_page(page, url: str) -> str:
    """Fetch a single URL using a real browser and return clean text."""
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"  ✗ Failed to load {url}: {e}")
        return ""

    # remove noise
    await page.evaluate("""
        const remove = ['script','style','nav','footer',
                        'header','noscript','iframe',
                        '.cookie-banner','.popup','.modal'];
        remove.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => el.remove());
        });
    """)

    # extract visible text
    text = await page.evaluate("""
        () => {
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null
            );
            const lines = [];
            let node;
            while (node = walker.nextNode()) {
                const line = node.textContent.trim();
                if (line.length > 20) lines.push(line);
            }
            return lines.join('\\n');
        }
    """)
    return text


async def scrape_all_banks(config_path: str = "banks_config.json") -> str:
    """
    Scrape all enabled banks from config and return one combined string.
    To add a new bank in the future — just add it to banks_config.json.
    No code changes needed here.
    """
    os.makedirs("data", exist_ok=True)
    banks = load_config(config_path)
    all_data_parts = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.set_extra_http_headers({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })

        for bank in banks:
            bank_name = bank["name"]
            topics = bank["pages"]

            print(f"\n── Scraping {bank_name} ──")
            bank_parts = [
                f"{'='*60}",
                f"BANK: {bank_name}",
                f"{'='*60}"
            ]

            for topic, urls in topics.items():
                topic_parts = [f"\n[{bank_name.upper()} — {topic.upper()}]"]

                for url in urls:
                    print(f"  Fetching: {url}")
                    text = await scrape_page(page, url)

                    if text:
                        topic_parts.append(f"\nSource: {url}")
                        topic_parts.append(text)
                        print(f"  ✓ Got {len(text)} characters")
                    else:
                        print(f"  ✗ No content retrieved")

                    await asyncio.sleep(2)

                bank_parts.extend(topic_parts)

            # save individual bank file
            bank_text = "\n".join(bank_parts)
            bank_file = f"data/{bank_name.lower().replace(' ', '_')}.txt"
            with open(bank_file, "w", encoding="utf-8") as f:
                f.write(bank_text)
            print(f"  ✓ Saved to {bank_file}")

            all_data_parts.append(bank_text)

        await browser.close()

    # combine into one string for the LLM system prompt
    combined = "\n\n".join(all_data_parts)
    with open("data/all_banks.txt", "w", encoding="utf-8") as f:
        f.write(combined)

    print(f"\n✓ Done. Total characters scraped: {len(combined)}")
    print(f"✓ Combined data saved to data/all_banks.txt")
    return combined


if __name__ == "__main__":
    asyncio.run(scrape_all_banks())