import json, urllib.request, sys

API = "http://127.0.0.1:8000"

def recent(limit=25):
    with urllib.request.urlopen(f"{API}/recent?limit={limit}") as r:
        return json.loads(r.read().decode())["rows"]

def refresh(id, notify=False):
    url = f"{API}/listing/{id}/refresh_comps" + ("?notify=true" if notify else "")
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def main(limit=25, notify=False):
    rows = recent(limit)
    for r in rows:
        out = refresh(r["id"], notify=notify)
        est = out.get("estimate", {})
        print(f'[{r["id"]}] {r["title"][:50]} → profit={est.get("profit")} roi%={est.get("roi_percent")} score={est.get("score")}')
    print("✅ rechecked")

if __name__ == "__main__":
    notify = "--notify" in sys.argv
    main(limit=25, notify=notify)
