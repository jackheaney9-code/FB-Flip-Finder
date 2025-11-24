import os, asyncio
from playwright.async_api import async_playwright

STORAGE_PATH = os.getenv("PLAYWRIGHT_STORAGE", "storage_state.json")

async def main():
    async with async_playwright() as p:
        # Ephemeral browser (no persistent profile -> no lock)
        browser = await p.chromium.launch(headless=False, args=["--no-sandbox"])
        context = await browser.new_context()  # brand-new context
        page = await context.new_page()

        # Go to the real (desktop) login page
        await page.goto("https://www.facebook.com/login", wait_until="domcontentloaded")
        print("➡️  In the window: log into Facebook (email + password + 2FA if asked).")
        print("   When you can see your feed or Marketplace, return here.")

        input("   Press Enter here to save the session... ")

        # Save cookies, localStorage, etc.
        await context.storage_state(path=STORAGE_PATH)
        print(f"✅ Saved {STORAGE_PATH}")

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
