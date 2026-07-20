# AGENTS.md

Architecture Studio: a Claude Code / Claude Desktop plugin marketplace of agents, skills, and rules for architects, designers, and AEC professionals. Content is Markdown, not application code.

## User-Facing Writing Style

Sacrifice grammar for concision. Fragments beat sentences. Cut articles, hedges, preamble, and restatement of the question.

- Drop "I've gone ahead and", "It looks like", "Great question", "Let me".
- Drop articles where meaning survives: "Config now points at new endpoint."
- Lead with the outcome. Caveats after, if at all.
- One idea per line. Prefer a fragment over a subordinate clause.
- Never pad to sound thorough. Length is not evidence of effort.

Bad: "I've gone ahead and updated the config file so that it now points to the new endpoint."
Good: "Config now points at new endpoint."

Bad: "It looks like the tests are currently failing, which appears to be because of a missing dependency."
Good: "Tests fail. Missing dep."

**Applies to:** chat replies, status updates, task summaries, commit bodies, PR descriptions, error copy, UI microcopy, release notes.

**Does not apply to:** code, code comments, ADRs, PRDs, or any spec where precision and full context outrank brevity. Never drop a qualifier that changes meaning - concision is not ambiguity.

Never use em dashes in public-facing copy. Use a spaced hyphen ( - ) instead.

## Commands

Repo lint. Structural checks over the Markdown and JSON surface. Same command CI runs.

```bash
./scripts/lint.sh
```

Deps: `jq`, `python3`, and PyYAML.

```bash
pip install pyyaml
```

## Layout

- `plugins/` - installable plugin bundles, numbered by project lifecycle. Skills live in `plugins/<n>-<name>/skills/<skill>/SKILL.md`; agents in `plugins/<n>-<name>/agents/`.
- `agents/` - agents index.
- `rules/` - cross-cutting conventions.
- `docs/adr/` - architecture decision records.
- `scripts/lint.sh` - the lint.
- `.claude-plugin/marketplace.json` - marketplace manifest listing every plugin and its source path.

Adding or renaming a plugin means updating `.claude-plugin/marketplace.json` and `README.md`.

## Conventions

- `SKILL.md` files require YAML frontmatter. `scripts/lint.sh` enforces it.
- `plugins/10-norma` shells out to the `norma` CLI. Never `python tools/...` directly, never grep a raw corpus path. Use `norma <verb>`. Lint enforces both.
