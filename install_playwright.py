import subprocess
import sys

def main():
    print("[BUILD] Installing Playwright Chromium (no OS deps)...")
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    print("[BUILD] Playwright Chromium install complete.")

if __name__ == "__main__":
    main()
