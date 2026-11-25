# handoff

Writes the previous context window's real conversation to a file the next window
reads before it answers.

## Why

When a context window fills up, the runtime summarises it and hands the summary
to the next window marked "reference only". That summary keeps the plot and
drops the detail that actually matters: what was underway, what was decided,
what is still open, what was touched.

The session database still has all of it. So read it directly, on a timer,
independent of any session surviving — and write the last stretch of verbatim
turns plus the questions that still look unanswered.

## Usage

```
python3 handoff.py                       # most recent session, 40 turns
python3 handoff.py --turns 60            # keep more of it
python3 handoff.py --session ID          # a specific session
python3 handoff.py --out ~/handoff.md    # where to write
```

Output is a markdown file with a header (session id, title, model, message
count), a **Still open** list, and the recent turns as `**User** timestamp —
text`. A sibling `.json` file carries the same metadata for tooling.

## Notes on the design

- **Read-only SQLite.** `?mode=ro` with a 5s timeout, so a writer holding the
  database can never be blocked by a status job.
- **Heuristic open questions.** The last three user messages minus obvious
  acknowledgements ("ok", "thanks", "cheers"). A slight over-capture beats a
  dropped thread — a stale question costs a glance, a lost one costs a day.
- **Truncated turns, not summarised ones.** 420 characters each. Summarising is
  what got us here.

## Configuration

| Variable | Default |
|---|---|
| `HANDOFF_DB` | `~/.centurion/state.db` |
| `HANDOFF_OUT` | `~/.centurion/state/handoff.md` |
| `HANDOFF_OWNER` | `User` — heading for user turns |
| `HANDOFF_AGENT` | `Assistant` — heading for agent turns |

## Scheduling

The point is that it runs whether or not a session is alive:

```
*/20 * * * * python3 ~/agent-toolkit/handoff/handoff.py >/dev/null 2>&1
```

Then have the agent read `handoff.md` at the top of a session if it is newer
than a few hours. That is the whole trick: stop asking the runtime to remember,
and write the thing down yourself.
