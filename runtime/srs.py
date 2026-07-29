#!/usr/bin/env python3
"""srs.py - a tiny Leitner spaced-repetition store for the learning loop (audit D2).
Cards live in comms/.srs/cards.json. Pure logic (no model, no network) so it's unit
tested. The learning agent surfaces DUE cards; grading moves them up/down the boxes."""
import os, sys, json, hashlib, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc

INTERVALS = {1: 1, 2: 2, 3: 4, 4: 7, 5: 15}   # box -> days until next review
PATH = os.path.join(fc.COMMS, ".srs", "cards.json")


def _today(today=None):
    return today or datetime.date.today()


def card_id(q):
    return hashlib.sha1(" ".join(q.lower().split()).encode()).hexdigest()[:6]


def load():
    try:
        return json.load(open(PATH, encoding="utf-8")).get("cards", {})
    except Exception:
        return {}


def save(cards):
    fc.atomic_write(PATH, json.dumps({"updated": fc.now(), "cards": cards}, indent=2))


def add_question(cards, q, today=None):
    """Add a new card (box 1, due today) if its text isn't already tracked."""
    q = q.strip()
    if not q:
        return None
    cid = card_id(q)
    if cid not in cards:
        d = _today(today).isoformat()
        cards[cid] = {"q": q, "box": 1, "due": d, "first_seen": d, "last_seen": ""}
    return cid


def due(cards, today=None):
    t = _today(today).isoformat()
    items = [(cid, c) for cid, c in cards.items() if c.get("due", t) <= t]
    items.sort(key=lambda kv: (kv[1].get("box", 1), kv[1].get("due", t)))
    return items


def mark_seen(cards, cid, today=None):
    if cid in cards:
        cards[cid]["last_seen"] = _today(today).isoformat()


def grade(cards, cid, correct, today=None):
    """correct -> promote a box (longer interval); wrong -> back to box 1 (tomorrow)."""
    c = cards.get(cid)
    if not c:
        return False
    t = _today(today)
    if correct:
        c["box"] = min(5, c.get("box", 1) + 1)
    else:
        c["box"] = 1
    c["due"] = (t + datetime.timedelta(days=INTERVALS[c["box"]])).isoformat()
    c["last_seen"] = t.isoformat()
    return True
