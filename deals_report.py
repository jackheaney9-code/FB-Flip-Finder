import json, urllib.request, csv, sys

API = "http://127.0.0.1:8000"

def recent(limit=100):
    with urllib.request.urlopen(f"{API}/recent?limit={limit}") as r:
        return json.loads(r.read().decode())["rows"]

def refresh(id):
    req = urllib.request.Request(f"{API}/listing/{id}/refresh_comps", method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def main(limit=50, out="deals.csv"):
    rows = recent(limit)
    scored = []
    for r in rows:
        j = refresh(r["id"])
        est = j.get("estimate",{})
        scored.append({
            "id": r["id"],
            "title": r["title"],
            "price": r.get("price"),
            "url": r.get("url"),
            "profit": est.get("profit"),
            "roi_percent": est.get("roi_percent"),
            "score": est.get("score"),
            "decision": est.get("decision"),
        })
    scored.sort(key=lambda x: (
        (x["score"] or -1),
        (x["profit"] or -1),
        (x["roi_percent"] or -1)
    ), reverse=True)

    with open(out,"w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=scored[0].keys())
        w.writeheader(); w.writerows(scored)
    print(f"✅ wrote {out} with {len(scored)} rows")
    # Print top 10 to console
    for s in scored[:10]:
        print(f'[{s["id"]}] {s["title"][:60]} | profit={s["profit"]} roi%={s["roi_percent"]} score={s["score"]} decision={s["decision"]}')
