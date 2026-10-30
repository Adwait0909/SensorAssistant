import json, os, sqlite3
from contextlib import closing
from pathlib import Path


def path():
    return Path(os.environ.get("CIRCUIT_DB", Path(__file__).resolve().parent.parent / "instance" / "circuits.db"))


def _conn():
    p = path(); p.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE IF NOT EXISTS circuits(id INTEGER PRIMARY KEY, created TEXT DEFAULT CURRENT_TIMESTAMP, name TEXT, components TEXT, valid INTEGER)")
    return c


def save(name, comps, valid):
    with closing(_conn()) as c, c:
        c.execute("INSERT INTO circuits(name,components,valid) VALUES(?,?,?)", (name, json.dumps(comps), int(valid)))


def recent(n=10):
    with closing(_conn()) as c:
        rows = c.execute("SELECT id,created,name,components,valid FROM circuits ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    return [{"id": r[0], "created": r[1], "name": r[2], "components": json.loads(r[3]), "valid": bool(r[4])} for r in rows]
