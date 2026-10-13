import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common import TRADES_CSV  # noqa: E402
from portfolio import fifo, load_trades, positions, totals  # noqa: E402
import prices  # noqa: E402


def T(ticker, date, side, qty, price):
    return {"ticker": ticker, "date": date, "side": side, "qty": qty, "price": price}


class FifoTest(unittest.TestCase):
    def test_partial_sell_uses_oldest_lot(self):
        tr = [T("A", "2025-01-01", "buy", 10, 100), T("A", "2025-02-01", "buy", 10, 200),
              T("A", "2025-03-01", "sell", 15, 300)]
        rows = positions(tr, {"A": {"price": 250, "prev": 240}})
        r = rows[0]
        self.assertEqual(r["qty"], 5)
        self.assertAlmostEqual(r["realized"], 10 * 200 + 5 * 100)
        self.assertAlmostEqual(r["avg"], 200)
        self.assertAlmostEqual(r["unreal"], 5 * 50)
        self.assertAlmostEqual(r["total"], 2500 + 250)
        self.assertAlmostEqual(r["realized_pct"], 2500 / (10 * 100 + 5 * 200) * 100)
        self.assertAlmostEqual(r["day_pct"], (250 / 240 - 1) * 100)

    def test_same_day_buy_before_sell(self):
        tr = [T("A", "2025-01-01", "sell", 5, 12), T("A", "2025-01-01", "buy", 5, 10)]
        p = fifo(tr)["A"]
        self.assertFalse(p["warn"])
        self.assertAlmostEqual(p["realized"], 10)

    def test_sell_without_buy_flags_warning(self):
        p = fifo([T("A", "2025-01-01", "sell", 5, 12)])["A"]
        self.assertTrue(p["warn"])

    def test_closed_position_has_zero_value(self):
        tr = [T("A", "2025-01-01", "buy", 2, 10), T("A", "2025-01-02", "sell", 2, 15)]
        r = positions(tr, {"A": {"price": 99, "prev": 98}})[0]
        self.assertEqual(r["qty"], 0)
        self.assertEqual(r["value"], 0)
        self.assertAlmostEqual(r["total"], 10)

    def test_missing_price_gives_none(self):
        r = positions([T("A", "2025-01-01", "buy", 2, 10)], {})[0]
        self.assertIsNone(r["value"])
        self.assertIsNone(r["total"])

    def test_totals(self):
        tr = [T("A", "2025-01-01", "buy", 1, 100), T("B", "2025-01-01", "buy", 1, 50)]
        rows = positions(tr, {"A": {"price": 110, "prev": 100}, "B": {"price": 40, "prev": 41}})
        t = totals(rows)
        self.assertAlmostEqual(t["value"], 150)
        self.assertAlmostEqual(t["unreal"], 0)

    def test_real_file_has_no_orphan_sells(self):
        per = fifo(load_trades(TRADES_CSV))
        self.assertEqual([k for k, v in per.items() if v["warn"]], [])


class ParseChartTest(unittest.TestCase):
    def test_parse(self):
        js = {"chart": {"result": [{"meta": {"regularMarketPrice": 10.5, "chartPreviousClose": 10.0,
                                              "regularMarketTime": 123}}]}}
        self.assertEqual(prices.parse_chart(js), (10.5, 10.0, 123))

    def test_no_price(self):
        js = {"chart": {"result": [{"meta": {}}]}}
        self.assertIsNone(prices.parse_chart(js))


if __name__ == "__main__":
    unittest.main()
