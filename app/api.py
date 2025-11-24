from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.encoders import jsonable_encoder
from decimal import Decimal
from typing import Optional, List
import sqlite3, os, csv, io

from .fbm_analyzer import analyze_fbm_url, save_listing
from .db import Base, engine, SessionLocal
from .models import Listing
from sqlalchemy import func
from .ebay_api import find_completed_items, summarize_prices
from .notify_email import send_deal_email
from .estimator import estimate_profit, decision_label
from .score import deal_score

Base.metadata.create_all(bind=engine)
app = FastAPI(title="FB Marketplace Analyzer")

@app.get("/health")
async def health():
    return {"ok": True}

# ---------- Day 1/2 endpoints ----------
@app.get("/analyze")
async def analyze(
    url: str = Query(..., description="Facebook Marketplace listing URL (must contain /marketplace/item/)"),
    headless: bool = Query(True, description="Run headless browser if true"),
):
    data = await analyze_fbm_url(url, headless=headless)
    saved = save_listing(data)
    return payload

@app.get("/analyze_full")
async def analyze_full(
    url: str = Query(..., description="Facebook Marketplace listing URL (must contain /marketplace/item/)"),
    headless: bool = Query(True, description="Run headless browser if true"),
):
    fb = await analyze_fbm_url(url, headless=headless)
    save_listing(fb)

    fb_title = fb.get("title") or ""
    fb_price = fb.get("price")
    fb_currency = fb.get("currency") or "CAD"

    comps = find_completed_items(fb_title, max_results=20)
    summary = summarize_prices(comps)

    est = estimate_profit(fb_price, summary["avg"], fee_rate=0.13)
    label = decision_label(est["profit"], est["roi_percent"])

        # compute a simple score for signal strength
    try:
        score = deal_score(fb_price, summary["avg"], summary["count"])
    except Exception:
        score = None

    # optional email if thresholds are met
    if notify and summary.get("avg") is not None and est.get("profit") is not None:
        import os
        PROFIT_BAR = float(os.getenv("NOTIFY_MIN_PROFIT", "40"))
        ROI_BAR    = float(os.getenv("NOTIFY_MIN_ROI", "35"))
        SCORE_BAR  = float(os.getenv("NOTIFY_MIN_SCORE", "20"))
        cond = (est["profit"] >= PROFIT_BAR) and ((est["roi_percent"] or 0) >= ROI_BAR)
        if score is not None:
            cond = cond or (score >= SCORE_BAR)
        if cond:
            subj = f"[FlipFinder] {label} — {row.title[:60]}"
            body = (

).format(
    title=row.title,
    fb_price=fb_price,
    avg=summary.get("avg"),
    count=summary.get("count"),
    profit=est.get("profit"),
    roi=est.get("roi_percent"),
    score=score,
    label=label,
    url=row.url,
)

def refresh_comps(listing_id: int, notify: bool = Query(False)):
    db = SessionLocal()
    try:
        row = db.query(Listing).get(listing_id)
        if not row:
            raise HTTPException(status_code=404, detail="Listing not found")

        title = row.title or ""
        fb_price = float(row.price) if row.price is not None else None

        comps = find_completed_items(title, max_results=20)
        summary = summarize_prices(comps)
        est = estimate_profit(fb_price, summary["avg"], fee_rate=0.13)
        label = decision_label(est["profit"], est["roi_percent"])

        # compute a simple deal score
        try:
            score = deal_score(fb_price, summary.get("avg"), summary.get("count", 0))
        except Exception:
            score = None

        # optional email trigger
        if notify and summary.get("avg") is not None and est.get("profit") is not None:
            import os
            PROFIT_BAR = float(os.getenv("NOTIFY_MIN_PROFIT", "40"))
            ROI_BAR    = float(os.getenv("NOTIFY_MIN_ROI", "35"))
            SCORE_BAR  = float(os.getenv("NOTIFY_MIN_SCORE", "20"))

            cond = (est["profit"] >= PROFIT_BAR) and ((est["roi_percent"] or 0) >= ROI_BAR)
            if score is not None:
                cond = cond or (score >= SCORE_BAR)

            if cond:
                subj = "[FlipFinder] {} — {}".format(label, (row.title or "")[:60])
                body = (
                    "Title: {title}\n"
                    "FB price: {fb_price}\n"
                    "eBay avg (USD): {avg} (count={count})\n"
                    "Profit est: {profit} | ROI%: {roi} | Score: {score}\n"
                    "Decision: {decision}\n"
                    "URL: {url}\n"
                ).format(
                    title=row.title,
                    fb_price=fb_price,
                    avg=summary.get("avg"),
                    count=summary.get("count"),
                    profit=est.get("profit"),
                    roi=est.get("roi_percent"),
                    score=score,
                    decision=label,
                    url=row.url,
                )
                _ = send_deal_email(subj, body)
    finally:
        db.close()

@app.post("/listing/{listing_id}/refresh_comps")
def refresh_comps(listing_id: int, notify: bool = Query(False)):
    db = SessionLocal()
    try:
        row = db.query(Listing).get(listing_id)
        if not row:
            raise HTTPException(status_code=404, detail="Listing not found")

        title = row.title or ""
        fb_price = float(row.price) if row.price is not None else None

        comps = find_completed_items(title, max_results=20)
        summary = summarize_prices(comps)
        est = estimate_profit(fb_price, summary["avg"], fee_rate=0.13)
        label = decision_label(est["profit"], est["roi_percent"])

        # compute a simple deal score
        try:
            score = deal_score(fb_price, summary.get("avg"), summary.get("count", 0))
        except Exception:
            score = None

        # optional email trigger
        if notify and summary.get("avg") is not None and est.get("profit") is not None:
            import os
            PROFIT_BAR = float(os.getenv("NOTIFY_MIN_PROFIT", "40"))
            ROI_BAR    = float(os.getenv("NOTIFY_MIN_ROI", "35"))
            SCORE_BAR  = float(os.getenv("NOTIFY_MIN_SCORE", "20"))

            cond = (est["profit"] >= PROFIT_BAR) and ((est["roi_percent"] or 0) >= ROI_BAR)
            if score is not None:
                cond = cond or (score >= SCORE_BAR)

            if cond:
                subj = "[FlipFinder] {} — {}".format(label, (row.title or "")[:60])
                body = (
                    "Title: {title}\n"
                    "FB price: {fb_price}\n"
                    "eBay avg (USD): {avg} (count={count})\n"
                    "Profit est: {profit} | ROI%: {roi} | Score: {score}\n"
                    "Decision: {decision}\n"
                    "URL: {url}\n"
                ).format(
                    title=row.title,
                    fb_price=fb_price,
                    avg=summary.get("avg"),
                    count=summary.get("count"),
                    profit=est.get("profit"),
                    roi=est.get("roi_percent"),
                    score=score,
                    decision=label,
                    url=row.url,
                )
                _ = send_deal_email(subj, body)
    finally:
        db.close()

# ---------- Day 3: browse/search/export ----------

def _sqlite_path_from_env() -> str:
    # Works for DATABASE_URL=sqlite:///flipfinder.db only (your default)
    url = os.getenv("DATABASE_URL", "sqlite:///flipfinder.db")
    return url.replace("sqlite:///","")

@app.get("/recent")
def recent(
    limit: int = Query(20, ge=1, le=100),
    label: str | None = Query(None, description="Filter by label (e.g., watch, buy, pass)"),
    min_price: float | None = Query(None, ge=0, description="Minimum price"),
    max_price: float | None = Query(None, ge=0, description="Maximum price"),
):
    db = SessionLocal()
    try:
        q = db.query(Listing)
        if label:
            q = q.filter(Listing.label == label)
        if min_price is not None:
            q = q.filter(Listing.price.isnot(None)).filter(Listing.price >= min_price)
        if max_price is not None:
            q = q.filter(Listing.price.isnot(None)).filter(Listing.price <= max_price)

        rows = q.order_by(Listing.id.desc()).limit(limit).all()
        out = []
        for r in rows:
            out.append({
                "id": r.id,
                "title": r.title,
                "price": float(r.price) if r.price is not None else None,
                "currency": r.currency,
                "url": r.url,
                "location": r.location,
                "label": r.label,
            })
        return {"rows": out}
    finally:
        db.close()

@app.get("/search")
def search(
    q: str = Query(..., min_length=2),
    limit: int = Query(25, ge=1, le=100),
    label: str | None = Query(None, description="Filter by label"),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
):
    db = SessionLocal()
    try:
        pat = f"%{q}%"
        qry = db.query(Listing).filter((Listing.title.ilike(pat)) | (Listing.description.ilike(pat)))
        if label:
            qry = qry.filter(Listing.label == label)
        if min_price is not None:
            qry = qry.filter(Listing.price.isnot(None)).filter(Listing.price >= min_price)
        if max_price is not None:
            qry = qry.filter(Listing.price.isnot(None)).filter(Listing.price <= max_price)

        rows = qry.order_by(Listing.id.desc()).limit(limit).all()
        out = []
        for r in rows:
            out.append({
                "id": r.id,
                "title": r.title,
                "price": float(r.price) if r.price is not None else None,
                "url": r.url,
                "label": r.label,
            })
        return {"rows": out, "query": q}
    finally:
        db.close()

@app.post("/listing/{listing_id}/note")
def set_note(listing_id: int, label: Optional[str] = None, note: Optional[str] = None):
    # write directly via sqlite to avoid orm/migration complexity
    dbfile = _sqlite_path_from_env()
    conn = sqlite3.connect(dbfile)
    cur = conn.cursor()
    # ensure columns exist
    for col, t in [("label","TEXT"), ("note","TEXT")]:
        cur.execute("PRAGMA table_info(listings)")
        cols = {r[1] for r in cur.fetchall()}
        if col not in cols:
            cur.execute(f"ALTER TABLE listings ADD COLUMN {col} {t}")
    cur.execute("SELECT id FROM listings WHERE id=?", (listing_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Listing not found")
    cur.execute("UPDATE listings SET label=COALESCE(?,label), note=COALESCE(?,note) WHERE id=?", (label, note, listing_id))
    conn.commit()
    conn.close()
    return {"ok": True, "id": listing_id, "label": label, "note": note}

@app.get("/export.csv")
def export_csv(limit: int = Query(200, ge=1, le=5000)):
    db = SessionLocal()
    try:
        rows = (
            db.query(Listing)
              .order_by(Listing.id.desc())
              .limit(limit)
              .all()
        )
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["id","title","price","currency","location","url"])
        for r in rows:
            w.writerow([
                r.id,
                (r.title or "").replace("\n"," ").strip(),
                float(r.price) if r.price is not None else "",
                r.currency or "",
                (r.location or "").replace("\n"," ").strip(),
                r.url or "",
            ])
        return PlainTextResponse(buf.getvalue(), media_type="text/csv")
    finally:
        db.close()

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def home():
    return """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>FlipFinder</title>
  <style>
    body { font-family: system-ui, Segoe UI, Roboto, Arial, sans-serif; margin: 24px; }
    h1 { margin: 0 0 12px; }
    .bar { display:flex; gap:8px; align-items:center; margin-bottom: 16px; flex-wrap: wrap; }
    input, button, select, textarea { padding: 8px; font-size: 14px; }
    table { border-collapse: collapse; width: 100%; margin-top: 16px; }
    th, td { border-bottom: 1px solid #eee; padding: 8px; text-align: left; vertical-align: top; }
    .small { color: #666; font-size: 12px; }
    .pill { padding: 2px 8px; border-radius: 12px; background: #f3f3f3; display: inline-block; font-size: 12px; }
    .row-actions { display:flex; gap:8px; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
  </style>
</head>
<body>
  <h1>FlipFinder</h1>
  
  <div class="bar">
    <input id="q" placeholder="Search title/description" style="min-width:260px">
    <select id="label">
      <option value="">All labels</option>
      <option value="watch">watch</option>
      <option value="buy">buy</option>
      <option value="pass">pass</option>
    </select>
    <input id="minp" placeholder="Min $" type="number" step="0.01" style="width:90px">
    <input id="maxp" placeholder="Max $" type="number" step="0.01" style="width:90px">
    <button onclick="doSearch()">Search</button>
    <button onclick="loadRecent()">Recent</button>
    <a class="pill" href="/export.csv?limit=200" target="_blank">Export CSV</a>
    <label class="pill" style="background:#eef">\
<input type="checkbox" id="notifyChk"> Email me good deals</label>
  </div>

  <div id="status" class="small"></div>
  <table id="tbl">
    <thead>
      <tr><th>ID</th><th>Title</th><th>Price</th><th>URL</th><th>Actions</th></tr>
    </thead>
    <tbody></tbody>
  </table>

  <pre id="out" class="mono"></pre>

<script>
async function jsonGET(u) {
  const r = await fetch(u);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
async function jsonPOST(u) {

  const r = await fetch(u, {method:'POST'});
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function getFiltersQS() {
  const l = document.getElementById('label')?.value || '';
  const minp = document.getElementById('minp')?.value || '';
  const maxp = document.getElementById('maxp')?.value || '';
  let qs = '';
  if (l) qs += '&label=' + encodeURIComponent(l);
  if (minp) qs += '&min_price=' + encodeURIComponent(minp);
  if (maxp) qs += '&max_price=' + encodeURIComponent(maxp);
  return qs;
}

function setStatus(t) { document.getElementById('status').textContent = t || ''; }

function rowHtml(r) {
  const price = (r.price==null) ? '' : `$${r.price}`;
  const url = r.url ? `<a href="${r.url}" target="_blank">open</a>` : '';
  return `
    <tr data-id="${r.id}">
      <td>${r.id}</td>
      <td>${(r.title||'').replaceAll('\n',' ')}</td>
      <td>${price}</td>
      <td>${url}</td>
      <td class="row-actions">
        <button onclick="refreshComps(${r.id})">Refresh comps</button>
        <button onclick="addNote(${r.id})">Add note</button>
      </td>
    </tr>`;
}

async function loadRecent() {
  setStatus('Loading recent…');
  try {
    const data = await jsonGET('/recent?limit=25' + getFiltersQS());
    const rows = data.rows || [];
    document.querySelector('#tbl tbody').innerHTML = rows.map(rowHtml).join('');
    setStatus(\`Showing \${rows.length} recent listings\`);
  } catch (e) { setStatus('Error: ' + e.message); }
}

async function doSearch() {
  const q = encodeURIComponent(document.getElementById('q').value.trim());
  if (!q) return loadRecent();
  setStatus('Searching…');
  try {
    const data = await jsonGET('/search?q=' + q + '&limit=50' + getFiltersQS());
    const rows = data.rows || [];
    document.querySelector('#tbl tbody').innerHTML = rows.map(rowHtml).join('');
    setStatus(\`Search "\${decodeURIComponent(q)}": \${rows.length} result(s)\`);
  } catch (e) { setStatus('Error: ' + e.message); }
}

async function refreshComps(id) {
  setStatus('Refreshing comps for #' + id + '…');
  try {
    const notify = document.getElementById('notifyChk')?.checked ? '?notify=true' : '';
    const res = await jsonPOST('/listing/' + id + '/refresh_comps' + notify);
    document.getElementById('out').textContent = JSON.stringify(res, null, 2);
    const c = res.ebay?.count ?? 0;
    const avg = res.ebay?.avg ?? null;
    const dec = res.estimate?.decision ?? '';
    setStatus(\`Comps: \${c} item(s); avg=\${avg ?? 'n/a'} | \${dec}\`);
  } catch (e) { setStatus('Error: ' + e.message); }
}

async function addNote(id) {
  const label = prompt('Label (e.g., watch, buy, pass):') || '';
  const note = prompt('Note text:') || '';
  setStatus('Saving note…');
  try {
    await jsonPOST('/listing/' + id + '/note?label=' + encodeURIComponent(label) + '&note=' + encodeURIComponent(note));
    setStatus('Saved label/note for #' + id);
  } catch (e) { setStatus('Error: ' + e.message); }
}
loadRecent();
</script>
</body>
</html>"""

@app.get("/labels")
def labels_counts():
    db = SessionLocal()
    try:
        rows = db.query(Listing.label, func.count(Listing.id)).group_by(Listing.label).all()
        return {"counts": [{"label": (lbl or ""), "count": cnt} for lbl, cnt in rows]}
    finally:
        db.close()

@app.post("/ebay-account-deletion")
def ebay_account_deletion(payload: dict):
    # Minimal handler for eBay Marketplace Account Deletion/Closure notifications.
    # You can log or act on it; for now we just acknowledge.
    try:
        print("eBay privacy event:", payload)
    except Exception:
        pass
    return {"ok": True}

def refresh_comps(listing_id: int, notify: bool = Query(False)):
    db = SessionLocal()
    try:
        row = db.query(Listing).get(listing_id)
        if not row:
            raise HTTPException(status_code=404, detail="Listing not found")

        title = row.title or ""
        fb_price = float(row.price) if row.price is not None else None

        comps = find_completed_items(title, max_results=20)
        summary = summarize_prices(comps)
        est = estimate_profit(fb_price, summary["avg"], fee_rate=0.13)
        label = decision_label(est["profit"], est["roi_percent"])

        # compute deal score
        try:
            score = deal_score(fb_price, summary.get("avg"), summary.get("count", 0))
        except Exception:
            score = None

        # optional email trigger
        if notify and summary.get("avg") is not None and est.get("profit") is not None:
            import os
            PROFIT_BAR = float(os.getenv("NOTIFY_MIN_PROFIT", "40"))
            ROI_BAR    = float(os.getenv("NOTIFY_MIN_ROI", "35"))
            SCORE_BAR  = float(os.getenv("NOTIFY_MIN_SCORE", "20"))

            cond = (est["profit"] >= PROFIT_BAR) and ((est["roi_percent"] or 0) >= ROI_BAR)
            if score is not None:
                cond = cond or (score >= SCORE_BAR)

            if cond:
                subj = "[FlipFinder] {} — {}".format(label, (row.title or "")[:60])
                body = (
                    "Title: {title}\n"
                    "FB price: {fb_price}\n"
                    "eBay avg (USD): {avg} (count={count})\n"
                    "Profit est: {profit} | ROI%: {roi} | Score: {score}\n"
                    "Decision: {decision}\n"
                    "URL: {url}\n"
                ).format(
                    title=row.title,
                    fb_price=fb_price,
                    avg=summary.get("avg"),
                    count=summary.get("count"),
                    profit=est.get("profit"),
                    roi=est.get("roi_percent"),
                    score=score,
                    decision=label,
                    url=row.url,
                )
                _ = send_deal_email(subj, body)
    finally:
        db.close()

def refresh_comps(listing_id: int, notify: bool = Query(False)):
    db = SessionLocal()
    try:
        row = db.query(Listing).get(listing_id)
        if not row:
            raise HTTPException(status_code=404, detail="Listing not found")

        title = row.title or ""
        fb_price = float(row.price) if row.price is not None else None

        comps = find_completed_items(title, max_results=20)
        summary = summarize_prices(comps)
        est = estimate_profit(fb_price, summary["avg"], fee_rate=0.13)
        label = decision_label(est["profit"], est["roi_percent"])

        # compute deal score
        try:
            score = deal_score(fb_price, summary.get("avg"), summary.get("count", 0))
        except Exception:
            score = None

        # optional email trigger
        if notify and summary.get("avg") is not None and est.get("profit") is not None:
            import os
            PROFIT_BAR = float(os.getenv("NOTIFY_MIN_PROFIT", "40"))
            ROI_BAR    = float(os.getenv("NOTIFY_MIN_ROI", "35"))
            SCORE_BAR  = float(os.getenv("NOTIFY_MIN_SCORE", "20"))

            cond = (est["profit"] >= PROFIT_BAR) and ((est["roi_percent"] or 0) >= ROI_BAR)
            if score is not None:
                cond = cond or (score >= SCORE_BAR)

            if cond:
                subj = "[FlipFinder] {} — {}".format(label, (row.title or "")[:60])
                body = (
                    "Title: {title}\n"
                    "FB price: {fb_price}\n"
                    "eBay avg (USD): {avg} (count={count})\n"
                    "Profit est: {profit} | ROI%: {roi} | Score: {score}\n"
                    "Decision: {decision}\n"
                    "URL: {url}\n"
                ).format(
                    title=row.title,
                    fb_price=fb_price,
                    avg=summary.get("avg"),
                    count=summary.get("count"),
                    profit=est.get("profit"),
                    roi=est.get("roi_percent"),
                    score=score,
                    decision=label,
                    url=row.url,
                )
                _ = send_deal_email(subj, body)
    finally:
        db.close()

