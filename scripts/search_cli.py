import os, sqlite3, sys, json

def main():
    if len(sys.argv) < 4:
        print("Usage: python scripts/search_cli.py '<query>' '<region substring>' <radius_km>")
        raise SystemExit(1)

    q = sys.argv[1].strip()
    region = sys.argv[2].strip()
    radius = float(sys.argv[3])
    if not (1 <= radius <= 1000):
        print("radius_km must be within 1–1000")
        raise SystemExit(1)

    db = os.getenv("DATABASE_URL","sqlite:///flipfinder.db").replace("sqlite:///","")
    con = sqlite3.connect(db); con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("""
      SELECT id, title, price, currency, url, location, distance_km
      FROM listings
      WHERE title LIKE '%'||?||'%' COLLATE NOCASE
        AND location LIKE '%'||?||'%' COLLATE NOCASE
        AND (distance_km IS NULL OR distance_km <= ?)
      ORDER BY id DESC
      LIMIT 100
    """, (q, region, radius))
    print(json.dumps([dict(r) for r in cur.fetchall()], indent=2, ensure_ascii=False))
    con.close()

if __name__ == "__main__":
    main()
