import asyncio, os, random, sys
from typing import List
from sqlalchemy.exc import IntegrityError
from app.fbm_analyzer import analyze_fbm_url, save_listing

# ---- knobs you can tweak ----
CONCURRENCY = int(os.getenv("FF_CONCURRENCY", "2"))   # run 1-3 in parallel; keep low
DELAY_MIN   = float(os.getenv("FF_DELAY_MIN", "1.5")) # seconds between tasks
DELAY_MAX   = float(os.getenv("FF_DELAY_MAX", "3.5"))
HEADLESS    = os.getenv("FF_HEADLESS", "false").lower() == "true"

async def worker(name: str, queue: asyncio.Queue):
    while True:
        url = await queue.get()
        try:
            data = await analyze_fbm_url(url, headless=HEADLESS)
            saved = save_listing(data)
            print(f"[{name}] {'SAVED' if saved else 'SKIPPED'} | {data.get('title')!r} | {url}")
        except IntegrityError:
            print(f"[{name}] DUPLICATE | {url}")
        except Exception as e:
            print(f"[{name}] ERROR | {url} | {e}")
        finally:
            # jitter between runs to be polite to FB
            await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            queue.task_done()

async def main(urls: List[str]):
    q = asyncio.Queue()
    for u in urls:
        u = u.strip()
        if u and "/marketplace/item/" in u:
            await q.put(u)
        else:
            print(f"SKIP (not a marketplace item): {u}")

    workers = [asyncio.create_task(worker(f"W{i+1}", q)) for i in range(CONCURRENCY)]
    await q.join()
    for w in workers:
        w.cancel()

if __name__ == "__main__":
    # Usage: python scripts/bulk_analyze.py urls.txt
    if len(sys.argv) < 2:
        print("Usage: python scripts/bulk_analyze.py <urls.txt>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        urls = [line.strip() for line in fh if line.strip()]
    asyncio.run(main(urls))
