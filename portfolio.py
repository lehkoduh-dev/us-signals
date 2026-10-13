"""Портфель: загрузка сделок и расчёт прибыли методом FIFO.

Комиссии и дивиденды в расчёт не входят.
"""
import csv
from collections import defaultdict, deque

EPS = 1e-9


def load_trades(path):
    trades = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            trades.append({
                "ticker": r["ticker"].strip().upper(),
                "date": r["date"].strip(),
                "side": r["side"].strip().lower(),
                "qty": float(r["qty"]),
                "price": float(r["price"]),
            })
    return trades


def load_watchlist(path):
    try:
        with open(path) as f:
            return [x.strip().upper() for x in f if x.strip() and not x.startswith("#")]
    except FileNotFoundError:
        return []


def fifo(trades):
    """Возвращает по тикеру: открытые лоты, реализованную прибыль и стоимость проданных лотов."""
    per = defaultdict(lambda: {"lots": deque(), "realized": 0.0, "sold_cost": 0.0, "warn": False})
    # в один день покупки считаются раньше продаж
    ordered = sorted(trades, key=lambda t: (t["date"], 0 if t["side"] == "buy" else 1))
    for t in ordered:
        p = per[t["ticker"]]
        if t["side"] == "buy":
            p["lots"].append([t["qty"], t["price"]])
            continue
        rem = t["qty"]
        while rem > EPS and p["lots"]:
            lot = p["lots"][0]
            used = min(rem, lot[0])
            p["realized"] += used * (t["price"] - lot[1])
            p["sold_cost"] += used * lot[1]
            lot[0] -= used
            rem -= used
            if lot[0] <= EPS:
                p["lots"].popleft()
        if rem > EPS:  # продажа без покупки в данных
            p["warn"] = True
    return per


def _ratio(a, b):
    return a / b if b else None


def positions(trades, prices):
    """prices: {ticker: {"price": float, "prev": float}}. Возвращает список строк по тикерам."""
    rows = []
    for tk, p in fifo(trades).items():
        qty = sum(l[0] for l in p["lots"])
        cost = sum(l[0] * l[1] for l in p["lots"])
        q = prices.get(tk) or {}
        px, prev = q.get("price"), q.get("prev")
        if qty <= EPS:
            qty, cost, value, unreal = 0.0, 0.0, 0.0, 0.0
        elif px is None:
            value, unreal = None, None
        else:
            value = qty * px
            unreal = value - cost
        realized = p["realized"]
        total = None if unreal is None else realized + unreal
        basis = p["sold_cost"] + cost
        rows.append({
            "ticker": tk,
            "qty": qty,
            "avg": _ratio(cost, qty),
            "price": px,
            "day_pct": (px / prev - 1) * 100 if px and prev else None,
            "value": value,
            "cost": cost,
            "realized": realized,
            "realized_pct": None if not p["sold_cost"] else realized / p["sold_cost"] * 100,
            "unreal": unreal,
            "unreal_pct": None if not cost or unreal is None else unreal / cost * 100,
            "total": total,
            "total_pct": None if not basis or total is None else total / basis * 100,
            "basis": basis,
            "sold_cost": p["sold_cost"],
            "warn": p["warn"],
        })
    return rows


def totals(rows):
    value = sum(r["value"] or 0 for r in rows)
    cost = sum(r["cost"] for r in rows)
    realized = sum(r["realized"] for r in rows)
    sold_cost = sum(r["sold_cost"] for r in rows)
    unreal = sum(r["unreal"] or 0 for r in rows)
    total = realized + unreal
    basis = sold_cost + cost
    return {
        "value": value,
        "cost": cost,
        "realized": realized,
        "realized_pct": None if not sold_cost else realized / sold_cost * 100,
        "unreal": unreal,
        "unreal_pct": None if not cost else unreal / cost * 100,
        "total": total,
        "total_pct": None if not basis else total / basis * 100,
    }
