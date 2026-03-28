# /csv-to-sif

Convert a CSV or Excel FF&E product list to SIF (Standard Interchange Format) for dealer and procurement systems. for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](../../../LICENSE)

## Install

```bash
# Via plugin system
claude plugin marketplace add AlpacaLabsLLC/skills-for-architects
claude plugin install 06-materials-research@skills-for-architects

# Or symlink just this skill
git clone https://github.com/AlpacaLabsLLC/skills-for-architects.git
ln -s $(pwd)/skills-for-architects/06-materials-research/skills/csv-to-sif ~/.claude/skills/csv-to-sif
```

## Usage

```
/csv-to-sif
```

## What's Included

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill definition and implementation |

## License

MIT
