import subprocess
import sys

def main():
    try:
        # Try installing Chromium with all dependencies (Linux-friendly)
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"])
    except Exception as e:
        # Fallback: try plain install if --with-deps isn't supported
        print("Fallback: trying 'playwright install chromium' without --with-deps")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

if __name__ == "__main__":
    main()
