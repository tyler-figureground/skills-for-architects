# ADR 0002: Atlas application code lives in tools/

Date: 2026-08-13
Status: Accepted

## Context

This repo is a Markdown plugin marketplace ("Content is Markdown, not application code" -
AGENTS.md). Atlas is a Python + Textual TUI/CLI that manages the studio's shared-drive
project folders (spec: `LIBRARY - Reference\_House Standard\atlas-tui-spec.md` on Google
Shared Drives). Tyler chose this repo as its home over a standalone `studio-atlas` repo or
Pyvoid: it is the architect-tooling home, and Atlas shares contracts with the plugins here -
`plugins/09-project-dossier` defines the `PROJECT.md` machine contract and `decisions/`
convention that Atlas scaffolds and audits.

## Decision

- Application code lives under `tools/atlas/` as a self-contained uv project (own
  `pyproject.toml`, `.venv`, tests). Nothing at repo root gains Python config.
- `tools/` is not a plugin: it is not listed in `.claude-plugin/marketplace.json` and
  `scripts/lint.sh` does not lint it. Atlas has its own quality gate: `uv run pytest`
  inside `tools/atlas/`.
- Contract sharing with Pyvoid stays test-enforced, not import-shared: the `PROJECT.md`
  byte-parity golden tests and the `^\d{6}` project-number convention are the shared
  invariants (spec section 7).

## Consequences

- One repo for architect tooling; plugin releases and Atlas releases stay independent
  (per-drive `.bat` shims pin an Atlas version).
- CI/lint surface unchanged for the marketplace; Atlas tests run separately.
- If a second application tool ever lands, `tools/<name>/` repeats this pattern.
