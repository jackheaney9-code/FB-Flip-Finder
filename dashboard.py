from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sqlite3
from pathlib import Path
from typing import List, Dict, Any

DB_PATH = Path("flipfinder.db")

app = FastAPI(title="FlipFinder – Raw Listings Viewer (DEBUG)")

def load_rows(limit: int = 200) -> List[Dict[str, Any]]:
    if not DB_PATH.exists():
        print("DB does not exist at:", DB_PATH.resolve())
        return []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM listings ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        print(f"Loaded {len(rows)} rows from {DB_PATH.resolve()}")
    except Exception as e:
        print("ERROR loading rows:", e)
        rows = []
    conn.close()
    return rows

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    rows = load_rows(limit=200)
    db_exists = DB_PATH.exists()
    db_abs = DB_PATH.resolve()
    row_count = len(rows)

    html_rows = ""
    for row in rows:
        id_ = row.get("id", "")
        title = (row.get("title") or "").replace("\n", " ")
        price = row.get("price", "")
        est_resale = row.get("estimated_resale", "")
        profit = row.get("profit", "")
        roi = row.get("roi", "")
        is_deal = row.get("is_deal", "")
        url = row.get("url", "")
        created_at = row.get("created_at", "")

        url_html = f'<a href="{url}" target="_blank">link</a>' if url else ""

        html_rows += f"""
        <tr>
          <td>{id_}</td>
          <td>{title[:100]}{"…" if title and len(title) > 100 else ""}</td>
          <td>{price}</td>
          <td>{est_resale}</td>
          <td>{profit}</td>
          <td>{roi}</td>
          <td>{is_deal}</td>
          <td>{url_html}</td>
          <td>{created_at}</td>
        </tr>
        """

    if not html_rows:
        html_rows = '<tr><td colspan="9">No rows found in listings table (DEBUG: row_count = 0).</td></tr>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <title>FlipFinder – Raw Listings (DEBUG)</title>
      <style>
        body {{
          font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          margin: 0;
          padding: 0;
          background: #0b0b10;
          color: #f5f5f7;
        }}
        header {{
          padding: 16px 24px;
          border-bottom: 1px solid #222;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }}
        h1 {{
          margin: 0;
          font-size: 20px;
        }}
        .badge {{
          font-size: 12px;
          padding: 4px 10px;
          border-radius: 999px;
          background: #1d1d27;
          border: 1px solid #333;
          color: #9ca3af;
        }}
        .container {{
          padding: 16px 24px 32px;
        }}
        table {{
          width: 100%;
          border-collapse: collapse;
          margin-top: 8px;
          font-size: 13px;
        }}
        thead {{
          background: #111827;
        }}
        th, td {{
          padding: 8px 10px;
          border-bottom: 1px solid #111827;
          vertical-align: top;
        }}
        th {{
          text-align: left;
          color: #9ca3af;
          font-weight: 500;
          white-space: nowrap;
        }}
        tr:nth-child(even) {{
          background: #050509;
        }}
        tr:hover {{
          background: #111827;
        }}
        a {{
          color: #60a5fa;
          text-decoration: none;
        }}
        a:hover {{
          text-decoration: underline;
        }}
        .debug {{
          font-size: 12px;
          color: #9ca3af;
          margin-top: 4px;
        }}
      </style>
    </head>
    <body>
      <header>
        <div>
          <h1>FlipFinder – Raw Listings (DEBUG)</h1>
          <div class="debug">
            DB exists: {db_exists} • Path: {db_abs} • Rows loaded: {row_count}
          </div>
        </div>
        <div class="badge">flipfinder.db</div>
      </header>
      <div class="container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Price</th>
              <th>Est. Resale</th>
              <th>Profit</th>
              <th>ROI</th>
              <th>Deal</th>
              <th>URL</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {html_rows}
          </tbody>
        </table>
      </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
