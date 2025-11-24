import json
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIE_PATH = "/tmp/fb_cookies.json"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 🔹 Go straight to Toronto Marketplace
        page.goto("https://www.facebook.com/marketplace/toronto", wait_until="networkidle")
        print("""
=== Facebook Toronto Marketplace helper ===
1. In the browser window:
   - Log into Facebook if you're not already.
   - Make sure you're seeing Marketplace in Toronto.
   - Click the location filter and confirm:
       • Location: Toronto, Ontario, Canada
       • Radius: up to 100 km (whatever FB allows)
   - Scroll down the feed a bit so the setting sticks.
2. When you're done, come back to this terminal.
""")
        input("When Marketplace is set to Toronto + radius and visible, press ENTER here... ")

        cookies = context.cookies()
        Path(COOKIE_PATH).write_text(json.dumps(cookies))
        print(f"✅ Cookies saved to: {COOKIE_PATH}")

        browser.close()

if __name__ == "__main__":
    main()
