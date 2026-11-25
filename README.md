# agent-toolkit

Small, dependency-free tools for running a long-lived AI agent on your own
hardware. Each one exists because a specific thing broke in daily use, and each
one is a single file you can read in a sitting.

| Tool | What it fixes |
|---|---|
| [`skill-find`](skill-find/) | You have 200 skills and no way to find the right one except reading the index and guessing. |
| [`evals`](evals/) | Every change to your persona, memory or prompts is judged by vibes. This makes it a number. |
| [`handoff`](handoff/) | A full context window destroys the working set, and the summary that replaces it keeps the plot and loses the detail. |

No pip install, no API keys except where noted, Python 3.9+, standard library
only.

---

## skill-find

BM25 search across every `SKILL.md` in a skills tree. Offline: no API, no
embeddings, no network.

```
skill-find "send email"
skill-find -n 10 "invoice overdue"
skill-find --json "browser automation"
skill-find --stats
```

Field-weighted so a skill whose *name* is the query beats one that mentions it in
paragraph nine — name ×4, tags ×3, description ×2, body ×1, with saturating term
frequency so repetition inside a body can never impersonate a name match. The
index is cached and rebuilds itself when any `SKILL.md` changes (mtime + size
fingerprint), so there is no "did you reindex?" step.

Reads `$SKILL_FIND_DIR`, default `~/.centurion/skills`. Index at
`~/.cache/skill-find/index.json`.

## evals

A behaviour regression suite. It assembles your real persona files plus a
standing-rules block, sends each scenario prompt through any OpenAI-compatible
endpoint, then has a second model grade the reply against explicit must-do and
must-not criteria. Results are written to `results/` as JSON, with ungraded
scenarios counted separately so a score can never quietly rise because a
scenario went unmeasured.

```
export EVALS_API_KEY=...        # any OpenAI-compatible provider
export EVALS_API_BASE=https://api.deepseek.com/v1
export EVALS_MODEL=deepseek-v4-flash
python3 run_evals.py --list
python3 run_evals.py --only brevity,no-re-raise
```

The shipped `scenarios.json` has 24 scenarios across verification, autonomy,
memory, delivery, ethics, identity, judgement, security and business categories.
Rewrite them for your own agent — the value is the shape, not these exact
prompts.

## handoff

Reads the session database and writes the previous window's actual conversation,
plus the open questions it can detect, to a markdown file the next window reads
before answering. Deliberately not a summary: summaries keep the plot and lose
the detail.

```
python3 handoff.py --turns 60 --out ~/handoff.md
```

Reads `$HANDOFF_DB` (default `~/.centurion/state.db`, read-only so it can never
block a writer), writes `$HANDOFF_OUT`. Set `HANDOFF_OWNER` and `HANDOFF_AGENT`
for the transcript headings.

---

## Install

No package to install. Clone and put what you want on your path:

```
git clone https://github.com/centurion-fleet/agent-toolkit.git
ln -s "$PWD/agent-toolkit/skill-find/skill-find" ~/.local/bin/skill-find
```

## Licence

AGPL-3.0-or-later. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

Built for [Centurion AI OS](https://github.com/centurion-fleet/Centurion-AI-OS-Brain),
but none of these tools require it.
