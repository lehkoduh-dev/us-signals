"""Общие настройки и доступ к SQLite."""
import os
import pathlib
import sqlite3

BASE = pathlib.Path(__file__).resolve().parent
DATA = pathlib.Path(os.environ.get("US_DATA", str(BASE / "data")))
TRADES_CSV = BASE / "portfolio_trades.csv"
WATCHLIST = BASE / "watchlist.txt"
SEC_UA = os.environ.get("SEC_UA", "PavelSignals lehkoduh@gmail.com")

SCHEMA = """
create table if not exists prices(
    ticker text primary key,
    price real,
    prev real,
    mtime integer,
    fetched integer
);
"""


def db():
    DATA.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DATA / "us.db", timeout=10)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con
