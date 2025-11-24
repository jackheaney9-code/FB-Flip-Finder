import csv, os, sqlite3, datetime, json, urllib.request, re

API = "http://127.0.0.1:8000"

def parse_price(s):
    if not s: return None
    m = re.search(r'(\d[\d,]*\.?\d*)', s)
    return float(m.group(1).replace(',', '')) if m else None

def insert_row(row):
    db = os.getenv("DATABASE_URL","sqlite:///flipfinder.db").replace("sqlite:///","")
    con = sqlite3.connect(db)
    cur = con.cursor()
    cols = [c[1] for c in cur.execute("PRAGMA table_info(listings)").fetchall()]
    now = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")

    data = {
        "title": row.get("title") or "",
        "price": parse_price(row.get("price")),
        "url": row.get("url"),
        "currency": row.get("currency") or "CAD",
        "location": row.get("location") or None,
        "label": "watch",
        "source": "facebook",
        "note": "csv import",
        "created_at": now,
    }
    keys = [k for k in data if k in cols]
    cur.execute(
        f"INSERT INTO listings ({','.join(keys)}) VALUES ({','.join(['?']*len(keys))})",
        [data[k] for k in keys]
    )
    con.commit()
    new_id = cur.execute("SELECT id FROM listings ORDER BY id DESC LIMIT 1").fetchone()[0]
    con.close()
    return new_id

def refresh(id, notify=True):
    url = f"{API}/listing/{id}/refresh_comps" + ("?notify=true" if notify else "")
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def main(path):
    added = []
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            if not row.get("url"): continue
            new_id = insert_row(row)
            out = refresh(new_id, notify=True)
            added.append((new_id, out.get("estimate",{})))
            print(f"ID {new_id} → {out.get('estimate')}")
    print(f"\n✅ imported {len(added)} listings")

if __name__ == "__main__":
    import sys
    if len(sys.argv)<2:
        print("usage: python bulk_add_from_csv.py watchlist.csv")
        raise SystemExit(2)
    main(sys.argv[1])
