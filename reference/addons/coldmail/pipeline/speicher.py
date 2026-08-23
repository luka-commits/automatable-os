#!/usr/bin/env python3
"""speicher.py — wo die Kohorte liegt. Supabase oder eine Datei, dieselbe API.

DER ANLASS (Luka, 23.08.2026): "brauchen wir eigentlich gar nicht Supabase, eine lokale SQL
haette doch auch gehen muessen, oder?" Fuer seine eigene Installation nicht -- das Portal liest
dieselbe Tabelle und kann keine Datei auf einem Laptop lesen. Fuer die Pipeline als **Add-on im
Automatable OS** dagegen schon, und dort ist es der Unterschied zwischen "Ordner auspacken und
loslegen" und "erst ein Supabase-Projekt anlegen, das Schema aufsetzen, Schluessel holen".

Ein Add-on darf fremde Dienste mitbringen, aber jeder zusaetzliche ist ein Grund mehr, nein zu
sagen. Cold Mail braucht ohnehin Apify, DataForSEO, Zapmail und Instantly -- eine Datenbank
obendrauf, die nur wir selbst lesen, ist der eine, den wir uns sparen koennen.

DIE ABSTRAKTION IST NICHT "POSTGREST AUF SQLITE". Das waere fragil: JSON-Pfade im `select`,
Range-Header, `Prefer`-Semantik. Sie ist stattdessen die Form, die die Pipeline ohnehin schon
hatte -- **lade die Kohorte, rechne in Python**. Jedes Skript hier holt sowieso 1000er-Seiten
und filtert lokal; gegen eine Datei ist das schneller als gegen HTTP, nicht langsamer.

    lade(niche=..., felder=[...])   -> list[dict]   die Kohorte
    lade_eins(place_id)             -> dict | None
    schreibe(zeilen)                -> int          upsert auf place_id
    aendere(place_id, **felder)     -> bool
    zaehle(niche=...)               -> int

Welches Backend, entscheidet `COLDMAIL_STORE`:
    supabase   (Vorgabe, wenn Zugangsdaten da sind)
    sqlite     eine Datei, Pfad in `COLDMAIL_DB` oder `context/.coldmail.db`

Selbsttest:  python3 speicher.py --self-check
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import urllib.parse
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
TABELLE = "industry_operators"

# Die Spalten, die keine JSON-Objekte tragen. Alles andere wird beim Schreiben nach
# JSON serialisiert und beim Lesen zurueckgeholt -- SQLite kennt keinen jsonb-Typ, und
# ein Dict, das als "{'a': 1}" (Python-repr, einfache Anfuehrungszeichen) in der Zelle
# landet, ist beim naechsten Lesen kein JSON mehr.
JSON_SPALTEN = {"raw", "raw_dataforseo", "web_signals", "details"}

SKALAR_SPALTEN = [
    "place_id", "name", "niche", "town", "region", "country", "website", "email",
    "phone", "lat", "lng", "reviews", "rating", "photos_count", "pipeline_status",
    "created_at", "updated_at",
]


# ─────────────────────────────────────────────────────────── Backend-Wahl
def _welches() -> str:
    wahl = (os.environ.get("COLDMAIL_STORE") or "").strip().lower()
    if wahl in ("sqlite", "supabase"):
        return wahl
    # Ohne ausdrueckliche Wahl: Supabase, wenn Zugangsdaten da sind, sonst die Datei.
    # Nicht umgekehrt -- wer Supabase eingerichtet hat, will es auch benutzen, und ein
    # stiller Wechsel auf eine leere lokale Datei sieht aus wie "alle Leads weg".
    try:
        _zugang()
        return "supabase"
    except SystemExit:
        return "sqlite"


def db_pfad() -> str:
    p = os.environ.get("COLDMAIL_DB")
    if p:
        return p
    return os.path.join(HIER, "..", "..", "..", "context", ".coldmail.db")


# ─────────────────────────────────────────────────────────── Supabase
def _zugang():
    """(url, key) aus der Portal-Env oder credentials.env. Kein Import-Zeit-Crash."""
    env = {}
    for p in (os.path.join(HIER.rsplit("/seo/", 1)[0], "seo/portal/.env.local"),
              os.path.expanduser("~/.config/credentials.env")):
        try:
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except FileNotFoundError:
            pass
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or env.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("keine Supabase-Zugangsdaten gefunden")
    return url, key


def _sb_lade(niche, felder, extra_filter):
    url, key = _zugang()
    hdr = {"apikey": key, "Authorization": f"Bearer {key}"}
    raus, off = [], 0
    while True:                                   # PostgREST liefert hoechstens 1000
        teile = [f"select={','.join(felder)}" if felder else "select=*"]
        if niche:
            teile.append(f"niche=eq.{urllib.parse.quote(niche, safe='')}")
        teile += list(extra_filter)
        teile += ["order=place_id", "limit=1000", f"offset={off}"]
        q = f"{url}/rest/v1/{TABELLE}?" + "&".join(teile)
        seite = json.load(urllib.request.urlopen(
            urllib.request.Request(q, headers=hdr), timeout=240))
        raus += seite
        if len(seite) < 1000:
            return raus
        off += 1000


def _sb_aendere(place_id, felder):
    url, key = _zugang()
    hdr = {"apikey": key, "Authorization": f"Bearer {key}",
           "Content-Type": "application/json", "Prefer": "return=minimal"}
    q = (f"{url}/rest/v1/{TABELLE}?place_id=eq."
         f"{urllib.parse.quote(str(place_id), safe='')}")
    req = urllib.request.Request(q, data=json.dumps(felder).encode(),
                                 method="PATCH", headers=hdr)
    urllib.request.urlopen(req, timeout=60).read()
    return True


def _sb_schreibe(zeilen):
    url, key = _zugang()
    hdr = {"apikey": key, "Authorization": f"Bearer {key}",
           "Content-Type": "application/json",
           "Prefer": "resolution=merge-duplicates,return=minimal"}
    n = 0
    for i in range(0, len(zeilen), 500):
        teil = zeilen[i:i + 500]
        req = urllib.request.Request(f"{url}/rest/v1/{TABELLE}",
                                     data=json.dumps(teil).encode(),
                                     method="POST", headers=hdr)
        urllib.request.urlopen(req, timeout=120).read()
        n += len(teil)
    return n


# ─────────────────────────────────────────────────────────── SQLite
def _con():
    p = db_pfad()
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    con = sqlite3.connect(p, timeout=30)
    con.row_factory = sqlite3.Row
    spalten = ", ".join(f'"{s}"' for s in SKALAR_SPALTEN if s != "place_id")
    jsons = ", ".join(f'"{s}"' for s in sorted(JSON_SPALTEN))
    con.execute(f'CREATE TABLE IF NOT EXISTS {TABELLE} ('
                f'place_id TEXT PRIMARY KEY, {spalten}, {jsons})')
    # Der eine Index, der zaehlt: jede Abfrage der Pipeline filtert auf die Nische.
    con.execute(f'CREATE INDEX IF NOT EXISTS ix_niche ON {TABELLE}(niche)')
    return con


def _zeile(r) -> dict:
    d = dict(r)
    for s in JSON_SPALTEN:
        if s in d and isinstance(d[s], str) and d[s]:
            try:
                d[s] = json.loads(d[s])
            except json.JSONDecodeError:
                d[s] = None
    return d


def _lt_lade(niche, felder, extra_filter):
    con = _con()
    try:
        wo, args = [], []
        if niche:
            wo.append("niche = ?")
            args.append(niche)
        # Die drei Filterformen, die die Pipeline wirklich benutzt. Alles darueber
        # hinaus gehoert nach Python, nicht in eine halbe Query-Sprache.
        for f in extra_filter:
            if f.startswith("pipeline_status=neq."):
                wo.append("coalesce(pipeline_status,'') != ?")
                args.append(f.split("neq.", 1)[1])
            elif f.startswith("pipeline_status=eq."):
                wo.append("pipeline_status = ?")
                args.append(f.split("eq.", 1)[1])
            elif f.startswith("place_id=eq."):
                wo.append("place_id = ?")
                args.append(urllib.parse.unquote(f.split("eq.", 1)[1]))
            elif f.startswith("region=eq."):
                wo.append("region = ?")
                args.append(urllib.parse.unquote(f.split("eq.", 1)[1]))
            else:
                raise ValueError(f"Filter kennt speicher.py nicht: {f!r}")
        sql = f"SELECT * FROM {TABELLE}"
        if wo:
            sql += " WHERE " + " AND ".join(wo)
        sql += " ORDER BY place_id"
        zeilen = [_zeile(r) for r in con.execute(sql, args)]
    finally:
        con.close()
    if felder:
        # Ein `select` mit JSON-Pfad ("s:raw_dataforseo->services") wird hier zur
        # ganzen Spalte -- der Aufrufer greift ohnehin in Python hinein.
        wunsch = {f.split(":")[-1].split("->")[0] for f in felder}
        zeilen = [{k: v for k, v in z.items() if k in wunsch} for z in zeilen]
    return zeilen


def _lt_schreibe(zeilen):
    if not zeilen:
        return 0
    con = _con()
    try:
        bekannt = set(SKALAR_SPALTEN) | JSON_SPALTEN
        n = 0
        for z in zeilen:
            d = {k: v for k, v in z.items() if k in bekannt}
            if not d.get("place_id"):
                continue
            for s in JSON_SPALTEN:
                if s in d and d[s] is not None and not isinstance(d[s], str):
                    d[s] = json.dumps(d[s], ensure_ascii=False)
            spalten = ", ".join(f'"{k}"' for k in d)
            frage = ", ".join("?" * len(d))
            setzen = ", ".join(f'"{k}"=excluded."{k}"' for k in d if k != "place_id")
            con.execute(f'INSERT INTO {TABELLE} ({spalten}) VALUES ({frage}) '
                        f'ON CONFLICT(place_id) DO UPDATE SET {setzen}',
                        list(d.values()))
            n += 1
        con.commit()
        return n
    finally:
        con.close()


def _lt_aendere(place_id, felder):
    con = _con()
    try:
        d = dict(felder)
        for s in JSON_SPALTEN:
            if s in d and d[s] is not None and not isinstance(d[s], str):
                d[s] = json.dumps(d[s], ensure_ascii=False)
        setzen = ", ".join(f'"{k}"=?' for k in d)
        cur = con.execute(f'UPDATE {TABELLE} SET {setzen} WHERE place_id=?',
                          list(d.values()) + [place_id])
        con.commit()
        return cur.rowcount > 0
    finally:
        con.close()


# ─────────────────────────────────────────────────────────── die eine API
def lade(niche: str = "", felder=None, ohne_disqualifiziert: bool = False,
         region: str = "", extra_filter=()) -> list:
    """Die Kohorte. Alle Zeilen auf einmal -- die Pipeline rechnet ohnehin lokal."""
    f = list(extra_filter)
    if ohne_disqualifiziert:
        f.append("pipeline_status=neq.disqualified")
    if region:
        f.append(f"region=eq.{urllib.parse.quote(region, safe='')}")
    if _welches() == "sqlite":
        return _lt_lade(niche, felder, f)
    return _sb_lade(niche, felder, f)


def lade_eins(place_id: str, felder=None):
    z = lade(felder=felder, extra_filter=[
        f"place_id=eq.{urllib.parse.quote(str(place_id), safe='')}"])
    return z[0] if z else None


def schreibe(zeilen: list) -> int:
    """Upsert auf place_id. -> Zahl der geschriebenen Zeilen."""
    if _welches() == "sqlite":
        return _lt_schreibe(zeilen)
    return _sb_schreibe(zeilen)


def aendere(place_id: str, **felder) -> bool:
    if not felder:
        return False
    if _welches() == "sqlite":
        return _lt_aendere(place_id, felder)
    return _sb_aendere(place_id, felder)


def zaehle(niche: str = "", ohne_disqualifiziert: bool = False) -> int:
    return len(lade(niche, ["place_id"], ohne_disqualifiziert))


def woher() -> str:
    """Was gerade benutzt wird -- fuer Meldungen, damit niemand ins Leere rechnet."""
    art = _welches()
    return "Supabase" if art == "supabase" else f"SQLite ({os.path.abspath(db_pfad())})"


# ─────────────────────────────────────────────────────────── Selbsttest
def self_check() -> int:
    """Gegen eine Wegwerf-Datei, nie gegen Supabase -- ein Selbsttest schreibt nichts
    in die Produktionskohorte."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        os.environ["COLDMAIL_STORE"] = "sqlite"
        os.environ["COLDMAIL_DB"] = os.path.join(d, "t.db")

        assert lade() == [], "leere Datei muss leer sein"
        n = schreibe([
            {"place_id": "a", "name": "Ace", "niche": "locksmith", "town": "Bedford",
             "raw": {"categories": ["Locksmith"], "reviewsCount": 9},
             "pipeline_status": None},
            {"place_id": "b", "name": "Gold", "niche": "locksmith",
             "pipeline_status": "disqualified", "raw": {"reviewsCount": 3}},
            {"place_id": "c", "name": "Rein", "niche": "cleaning", "raw": None},
        ])
        assert n == 3, n

        alle = lade("locksmith")
        assert len(alle) == 2, alle
        # JSON kommt als Objekt zurueck, nicht als Zeichenkette -- daran waere sonst
        # jede `raw.get(...)`-Zeile der Pipeline gescheitert.
        assert alle[0]["raw"]["categories"] == ["Locksmith"], alle[0]["raw"]
        assert alle[0]["raw"]["reviewsCount"] == 9

        offen = lade("locksmith", ohne_disqualifiziert=True)
        assert [z["place_id"] for z in offen] == ["a"], offen

        eins = lade_eins("a")
        assert eins and eins["name"] == "Ace"
        assert lade_eins("gibtsnicht") is None

        # Upsert ueberschreibt, legt nicht doppelt an
        schreibe([{"place_id": "a", "name": "Ace Locks", "niche": "locksmith"}])
        assert len(lade("locksmith")) == 2
        assert lade_eins("a")["name"] == "Ace Locks"
        # und laesst Felder in Ruhe, die es nicht nennt
        assert lade_eins("a")["raw"]["reviewsCount"] == 9, "Upsert hat raw geloescht"

        assert aendere("a", web_signals={"mail": {"tip_1": "- x"}}) is True
        assert lade_eins("a")["web_signals"]["mail"]["tip_1"] == "- x"
        assert aendere("gibtsnicht", name="x") is False

        assert zaehle("locksmith") == 2
        assert zaehle("locksmith", ohne_disqualifiziert=True) == 1

        # Nur die verlangten Felder, und ein JSON-Pfad-select bringt die ganze Spalte
        schmal = lade("locksmith", ["place_id", "name"])
        assert set(schmal[0]) == {"place_id", "name"}, schmal[0]
        pfad = lade("locksmith", ["s:raw->reviewsCount"])
        assert "raw" in pfad[0], pfad[0]

        try:
            lade(extra_filter=["irgendwas=like.*"])
            raise AssertionError("unbekannter Filter muss auffallen, nicht durchrutschen")
        except ValueError:
            pass
    print("speicher self-check ok")
    return 0


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        sys.exit(self_check())
    print(f"Speicher: {woher()}")
