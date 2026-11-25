# skill-find

BM25 keyword search over every `SKILL.md` in a skills tree. One file, standard
library only, no network.

## Why

An agent with 200+ skills has a retrieval problem, not an authoring problem. The
only ways to find the right skill are to read the whole index and hope, or to
guess a name. Both fail at exactly the moment it matters — when the skill you
need is one you forgot the name of.

Embeddings solve this, but they cost an API call per query, need a vector store,
and go stale silently. For a corpus of a few hundred short documents, lexical
search done properly is enough and has no failure mode beyond "no match".

## Design

- **Field weighting** — name ×4, tags ×3, description ×2, body ×1. A skill
  called `email-send` should beat one that mentions email in paragraph nine.
- **Saturating term frequency** — `1 + log(count)` per field, so four mentions
  in a body cannot impersonate a single name match.
- **Body cap** — the first 1,200 body tokens only, so one enormous SKILL.md
  cannot distort the corpus statistics.
- **Crude suffix stemming** — enough for `skills`/`skill` and `loading`/`load` to
  collide. Consistency matters more than linguistic purity.
- **Self-invalidating index** — mtime and size fingerprint per file; the index
  rebuilds on the next query when anything changed. No reindex step to forget.
- **Dot-directories skipped** — archived skills are not loadable, and sending
  someone to a skill they cannot load is worse than no result.

## Usage

```
skill-find "<query>"            top 5, with score and why
skill-find -n 10 "<query>"      more
skill-find --json "<query>"     machine-readable
skill-find --rebuild "<query>"  force a rebuild
skill-find --stats              corpus and index state
```

Output says *why* each hit ranked, which field carried it:

```
1. email-send      5.13  name+desc+body: send, email (2/2 terms)
2. himalaya        4.61  tags+desc+body: email, send (2/2 terms)
```

## Configuration

| Variable | Default |
|---|---|
| `SKILL_FIND_DIR` | `~/.centurion/skills` |
| `XDG_CACHE_HOME` | `~/.cache` (index at `<cache>/skill-find/index.json`) |

## Install

```
install -m 755 skill-find ~/.local/bin/skill-find
```

Works on any tree of `SKILL.md` files with optional YAML frontmatter
(`name:`, `description:`, `tags: [...]`). Missing frontmatter is tolerated — the
directory name is used instead.
