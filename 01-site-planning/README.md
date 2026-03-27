# Site Planning

A Claude Code plugin for site research and due diligence. Give it an address and it builds a comprehensive site analysis — climate, transit, demographics, history, and zoning — using public data sources. What used to take days of manual research happens in minutes.

## The Problem

Early-stage site analysis requires pulling data from dozens of sources — NOAA for climate, Census Bureau for demographics, MTA for transit, Landmarks Preservation for historic districts, PLUTO for zoning. Architects and developers spend days assembling this into a coherent picture before design can even begin.

## The Solution

Four research skills that each investigate a different dimension of a site, plus a command that runs them all in sequence for full due diligence. Each skill searches authoritative public data sources, synthesizes findings, and outputs a structured markdown report.

```
                                    ┌─────────────┐
                                    │   Address   │
                                    └──────┬──────┘
                                           │
         ┌─────────────┬───────────────────┼───────────────────┐
         │             │                   │                   │
         ▼             ▼                   ▼                   ▼
  ┌────────────┐ ┌────────────┐ ┌──────────────────┐ ┌──────────────────┐
  │Environmental│ │  Mobility  │ │  Demographics    │ │  History         │
  │            │ │            │ │                  │ │                  │
  │ Climate    │ │ Transit    │ │ Population       │ │ Adjacent uses    │
  │ Precip.    │ │ Walk/Bike/ │ │ Income           │ │ Arch. character  │
  │ Wind       │ │ Transit    │ │ Age distribution │ │ Historic dist.   │
  │ Sun angles │ │ scores     │ │ Housing market   │ │ Landmarks        │
  │ Flood zones│ │ Major roads│ │ Employment       │ │ Commercial       │
  │ Seismic    │ │ Airport    │ │                  │ │ Planned devt.    │
  │ Soil & topo│ │ Ped. infra.│ │                  │ │                  │
  └─────┬──────┘ └─────┬──────┘ └────────┬─────────┘ └────────┬─────────┘
        │              │                 │                     │
        ▼              ▼                 ▼                     ▼
  ┌────────────────────────────────────────────────────────────────────┐
  │                      Markdown Reports                            │
  │                                                                  │
  │  One file per analysis, each with:                               │
  │  Key Metrics table + detailed sections                           │
  └──────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Input

Every research skill takes a single input: **an address or location**. It asks once, then researches autonomously without interrupting.

### Research sources

Each skill searches authoritative, governmental, and non-profit sources:

| Skill | Primary sources |
|-------|----------------|
| Environmental | NOAA, USGS, EPA, NWS, NREL |
| Mobility | MTA, DOT, Walk Score, FAA, USDOT |
| Demographics | Census Bureau, BLS, HUD, NYC Open Data |
| History | NYC LPC, National Register, DCP, Library of Congress |

### Output

Each skill produces a **structured markdown report** with a Key Metrics summary table followed by detailed sections. Reports are saved to local files.

### Pipeline

The `/site-due-diligence-nyc` command runs all four research skills plus NYC zoning in sequence, carrying context forward between steps:

```
Address → Environmental → Mobility → Demographics → History → Zoning → 5 reports
```

## Skills

| Skill | Description |
|-------|-------------|
| [environmental-analysis](skills/environmental-analysis/) | Climate and environmental conditions — temperature, precipitation, wind, sun, flood zones, seismic risk, soil, topography |
| [mobility-analysis](skills/mobility-analysis/) | Transit and mobility — subway, bus, bike, pedestrian infrastructure, walk/bike/transit scores, airport access |
| [demographics-analysis](skills/demographics-analysis/) | Demographics and market — population, income, age distribution, housing market, employment |
| [history](skills/history/) | Neighborhood context — adjacent uses, architectural character, landmarks, commercial activity, planned development |


## Commands

| Command | Description |
|---------|-------------|
| [site-due-diligence-nyc](commands/site-due-diligence-nyc.md) | Full NYC site due diligence — environmental, mobility, demographics, history, and zoning from PLUTO |

## Install

**Claude Desktop:**

1. Open the **+** menu → **Add marketplace from GitHub**
2. Enter `AlpacaLabsLLC/skills-for-architects`
3. Install the **Site Planning** plugin

**Claude Code (terminal):**

```bash
claude plugin marketplace add AlpacaLabsLLC/skills-for-architects
claude plugin install 01-site-planning@skills-for-architects
```

**Manual:**

```bash
git clone https://github.com/AlpacaLabsLLC/skills-for-architects.git
ln -s $(pwd)/skills-for-architects/01-site-planning/skills/environmental-analysis ~/.claude/skills/environmental-analysis
```

## License

MIT
