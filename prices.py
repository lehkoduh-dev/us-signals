"""Цены: Yahoo Finance chart API, кеш 10 минут в SQLite."""
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from common import db

TTL = 600
UA = os.environ.get("YAHOO_UA", "Mozilla/5.0")  # длинный браузерный UA ловит 429, короткий проходит
URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
_lock = threading.Lock()


def parse_chart(js):
    """Возвращает (цена, предыдущее закрытие, время котировки) или None."""
    res = js["chart"]["result"][0]
    m = res["meta"]
    price = m.get("regularMarketPrice")
    prev = m.get("chartPreviousClose") or m.get("previousClose")
    if price is None:
        return None
    return price, prev, m.get("regularMarketTime")


def fetch_one(ticker, retries=3):
    """Один запрос к Yahoo; при 429 ждём и повторяем."""
    for attempt in range(retries):
        r = requests.get(URL.format(ticker), params={"range": "1d", "interval": "1d"},
                         headers={"User-Agent": UA}, timeout=15)
        if r.status_code == 429 and attempt < retries - 1:
            time.sleep(2 * (attempt + 1))
            continue
        r.raise_for_status()
        return parse_chart(r.json())


def refresh(tickers, force=False):
    """Обновляет устаревшие цены и возвращает {ticker: {price, prev, mtime, fetched}}."""
    with _lock:
        now = int(time.time())
        con = db()
        have = {r["ticker"]: r["fetched"] for r in con.execute("select ticker, fetched from prices")}
        todo = [t for t in tickers if force or now - (have.get(t) or 0) >= TTL]

        def work(t):
            try:
                return t, fetch_one(t)
            except Exception as e:  # сеть/лимит: оставляем старую цену
                print("price fail", t, e, flush=True)
                return t, None

        if todo:
            with ThreadPoolExecutor(3) as ex:  # без пачки запросов, чтобы не ловить 429
                results = list(ex.map(work, todo))
            for t, v in results:
                if v:
                    con.execute("insert or replace into prices values(?,?,?,?,?)",
                                (t, v[0], v[1], v[2], now))
            con.commit()
        out = {r["ticker"]: dict(r) for r in con.execute("select * from prices")}
        con.close()
        return out
