"""Веб-сервер US Market Signals (личное использование, порт 8081)."""
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import prices
from common import BASE, TRADES_CSV, WATCHLIST
from portfolio import load_trades, load_watchlist, positions, totals

PORT = int(os.environ.get("PORT", "8081"))


def universe(trades):
    seen, out = set(), []
    for t in [x["ticker"] for x in trades] + load_watchlist(WATCHLIST):
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def build():
    trades = load_trades(TRADES_CSV)
    tickers = universe(trades)
    px = prices.refresh(tickers)
    rows = positions(trades, px)
    by = {r["ticker"]: r for r in rows}
    total_value = sum(r["value"] or 0 for r in rows)
    allrows = []
    for tk in tickers:
        r = by.get(tk)
        q = px.get(tk) or {}
        price, prev = q.get("price"), q.get("prev")
        value = r["value"] if r else 0.0
        allrows.append({
            "ticker": tk,
            "price": price,
            "day_pct": (price / prev - 1) * 100 if price and prev else None,
            "qty": r["qty"] if r else 0.0,
            "value": value,
            "weight": value / total_value * 100 if total_value and value else 0.0,
        })
    mine = [r for r in rows if r["qty"] > 0]
    closed = [r for r in rows if r["qty"] == 0]
    newest = max([q["fetched"] for q in px.values()] or [0])
    return {"mine": mine, "closed": closed, "totals": totals(rows), "all": allrows,
            "updated": newest, "now": int(time.time())}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        data = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        try:
            if path in ("/", "/index.html"):
                self._send(200, (BASE / "page.html").read_bytes(), "text/html; charset=utf-8")
            elif path == "/api/data":
                self._send(200, json.dumps(build()), "application/json")
            elif path == "/health":
                self._send(200, "ok", "text/plain")
            else:
                self._send(404, "not found", "text/plain")
        except Exception as e:
            print("error", path, e, flush=True)
            self._send(500, json.dumps({"error": str(e)}), "application/json")

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print(f"US Market Signals on :{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
