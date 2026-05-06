# Changelog

All notable changes to **Architecture Studio** (`AlpacaLabsLLC/skills-for-architects`) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `.gitignore` covering macOS, editor, and local-env artifacts.
- `scripts/lint.sh` — repo lint script with six structural checks: no tracked `.DS_Store`, JSON validity, SKILL.md frontmatter (`name` + `description` required), count consistency (plugins, per-plugin skill counts, marketplace.json), internal markdown link resolution, and shellcheck on `hooks/*.sh`.
- `.github/workflows/lint.yml` — runs `scripts/lint.sh` on push to `main` and on every PR.

### Removed

- 11 tracked `.DS_Store` files. Now ignored repo-wide via `.gitignore`.

## [1.0.0] - 2026-05-06

First public release.

### Added

- **7 agents** — `site-planner`, `nyc-zoning-expert`, `workplace-strategist`, `product-and-materials-researcher`, `ffe-designer`, `sustainability-specialist`, `brand-manager`.
- **35 skills** across **9 plugins**:
  - `00-due-diligence` (7) — NYC landmarks, DOB permits, DOB violations, ACRIS, HPD, BSA, combined property report.
  - `01-site-planning` (4) — environmental, mobility, demographics, history.
  - `02-zoning-analysis` (2) — `/zoning-analysis-nyc` (PLUTO + Zoning Resolution), `/zoning-envelope` (Three.js 3D viewer).
  - `03-programming` (2) — workplace programmer, IBC occupancy calculator.
  - `04-specifications` (1) — CSI MasterFormat outline specs.
  - `05-sustainability` (4) — EPD parse, research, compare, spec.
  - `06-materials-research` (12) — product research, spec extraction, schedule cleanup, image processing, master schedule, SIF crosswalk.
  - `07-presentations` (3) — slide decks, color palettes, image resizing.
  - `08-dispatcher` (2) — `/studio` router, `/skills` menu.
- **7 rules** — units & measurements, code citations, professional disclaimer, CSI formatting, terminology, output formatting, transparency.
- **3 hooks** — post-write disclaimer check, post-output metadata, pre-commit spec lint.
- Marketplace install: `claude plugin marketplace add AlpacaLabsLLC/skills-for-architects`.

[Unreleased]: https://github.com/AlpacaLabsLLC/skills-for-architects/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/AlpacaLabsLLC/skills-for-architects/releases/tag/v1.0.0
