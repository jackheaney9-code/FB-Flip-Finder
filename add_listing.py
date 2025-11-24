import os, sys, json, sqlite3, datetime, urllib.request

API = "http://127.0.0.1:8000"

def parse_price(s):
    if s is None: return None
    # pull digits/decimal from strings like "$250", "CA$1,999.00"
    import re
    m = re.search(r'(\d[\d,]*\.?\d*)', s)
    return float(m.group(1).replace(',', '')) if m else None

def insert_listing(title, price, url, currency="CAD", location=None, label=None, note=None, source="facebook"):
    db = os.getenv("DATABASE_URL","sqlite:///flipfinder.db").replace("sqlite:///","")
    con = sqlite3.connect(db)
    cur = con.cursor()
    cols = [c[1] for c in cur.execute("PRAGMA table_info(listings)").fetchall()]

    now = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
    row = {
        "title": title,
        "price": price,
        "url": url,
        "currency": currency,
        "location": location,
        "label": label,
        "note": note,
        "source": source,
        "created_at": now,
    }
    avail = [k for k in row if k in cols]
    sql = "INSERT INTO listings ({}) VALUES ({})".format(",".join(avail), ",".join(["?"]*len(avail)))
    cur.execute(sql, [row[k] for k in avail])
    con.commit()
    new_id = cur.execute("SELECT id FROM listings ORDER BY id DESC LIMIT 1").fetchone()[0]
    con.close()
    return new_id

def refresh(id, notify=True):
    url = f"{API}/listing/{id}/refresh_comps" + ("?notify=true" if notify else "")
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def main():
    if len(sys.argv) < 3:
        print("usage: python add_listing.py '<facebook url>' '<title>' [price] [currency] [location]")
        sys.exit(2)
    fb_url   = sys.argv[1]
    title    = sys.argv[2]
    price    = parse_price(sys.argv[3]) if len(sys.argv) >= 4 else None
    currency = sys.argv[4] if len(sys.argv) >= 5 else "CAD"
    location = sys.argv[5] if len(sys.argv) >= 6 else None

    new_id = insert_listing(title, price, fb_url, currency=currency, location=location)
    print("Inserted ID:", new_id)
    out = refresh(new_id, notify=True)
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
