#!/usr/bin/env python3
"""Write a structured handoff of the live working set, so context compaction
stops destroying the morning.

Why this exists: when a window fills up the brain summarises it and tells the
next window the summary is "reference only" — which is a polite way of saying
the working set is gone. The summary keeps the plot and loses the detail that
actually matters: what was underway, what was decided, what is still open, what
was touched.

This reads the session database directly and writes the last stretch of real
conversation, plus the open questions, to a markdown file the next window reads
before answering. It runs on a timer, independent of any session surviving.

  python3 handoff.py                # most recent session
  python3 handoff.py --session ID   # a specific session
  python3 handoff.py --turns 60     # how many turns of history to keep
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import time

HOME = os.path.expanduser("~")
DB = os.environ.get("HANDOFF_DB") or os.path.join(HOME, ".centurion", "state.db")
OUT = os.environ.get("HANDOFF_OUT") or os.path.join(HOME, ".centurion", "state", "handoff.md")
JSON_OUT = os.path.splitext(OUT)[0] + ".json"

# Names used in the transcript headings. Set these to your own.
OWNER = os.environ.get("HANDOFF_OWNER") or "User"
AGENT = os.environ.get("HANDOFF_AGENT") or "Assistant"

# Turns this recent are worth carrying verbatim; older material is what
# session_search is for.
DEFAULT_TURNS = 40
TRUNC = 420


def connect():
    # Read-only so a writer holding the file can never be blocked by us.
    uri = f"file:{DB}?mode=ro"
    con = sqlite3.connect(uri, uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    return con


def latest_session(con):
    row = con.execute(
        "SELECT session_id, MAX(timestamp) AS last FROM messages "
        "GROUP BY session_id ORDER BY last DESC LIMIT 1").fetchone()
    return row["session_id"] if row else None


def session_meta(con, sid):
    try:
        r = con.execute("SELECT * FROM sessions WHERE id = ?", (sid,)).fetchone()
        return dict(r) if r else {}
    except Exception:
        return {}


def turns(con, sid, limit):
    rows = con.execute(
        "SELECT role, content, timestamp, tool_name FROM messages "
        "WHERE session_id = ? AND role IN ('user','assistant') "
        "ORDER BY id DESC LIMIT ?", (sid, limit)).fetchall()
    return list(reversed(rows))


def clip(text, n=TRUNC):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text if len(text) <= n else text[: n - 1] + "…"


def open_questions(rows):
    """User messages that read as a request still awaiting an answer.

    Heuristic, deliberately: the last three things asked, minus anything that
    was clearly a closed acknowledgement. Better a slight over-capture than a
    dropped thread.
    """
    out = []
    for r in reversed(rows):
        if r["role"] != "user":
            continue
        text = clip(r["content"], 200)
        if not text:
            continue
        if re.fullmatch(r"(ok|okay|thanks|thank you|great|good|nice|cheers)[.!]?",
                        text.strip(), re.I):
            continue
        out.append(text)
        if len(out) >= 3:
            break
    return list(reversed(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="")
    ap.add_argument("--turns", type=int, default=DEFAULT_TURNS)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    global OUT, JSON_OUT
    if args.out:
        OUT = os.path.expanduser(args.out)
        JSON_OUT = os.path.splitext(OUT)[0] + ".json"

    if not os.path.exists(DB):
        print(f"no session db at {DB}", file=sys.stderr)
        return 1

    con = connect()
    sid = args.session or latest_session(con)
    if not sid:
        print("no sessions found", file=sys.stderr)
        return 1

    meta = session_meta(con, sid)
    rows = turns(con, sid, args.turns)
    if not rows:
        print(f"no turns for session {sid}", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    now = time.strftime("%Y-%m-%d %H:%M:%S %Z")

    lines = [
        "# Handoff — live working set",
        "",
        f"Generated: {now}  ",
        f"Session: `{sid}` — {meta.get('title') or 'untitled'}  ",
        f"Model: {meta.get('model') or '?'} · messages: {meta.get('message_count') or len(rows)} "
        f"· started: {meta.get('started_at') or '?'}",
        "",
        "This is the previous window's actual conversation, not a summary of it.",
        "Read it before answering; use session_search for anything older.",
        "",
        "## Still open",
        "",
    ]
    qs = open_questions(rows)
    lines += [f"- {q}" for q in qs] if qs else ["- (nothing outstanding detected)"]
    lines += ["", "## Recent turns", ""]
    for r in rows:
        who = OWNER if r["role"] == "user" else AGENT
        stamp = str(r["timestamp"] or "")[:19]
        lines.append(f"**{who}** `{stamp}` — {clip(r['content'])}")
        lines.append("")

    open(OUT, "w", encoding="utf-8").write("\n".join(lines))

    json.dump({
        "generated_at": now,
        "session_id": sid,
        "title": meta.get("title"),
        "model": meta.get("model"),
        "open_questions": qs,
        "turn_count": len(rows),
    }, open(JSON_OUT, "w", encoding="utf-8"), indent=2)

    print(f"handoff written: {OUT} ({len(rows)} turns, {len(qs)} open)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
