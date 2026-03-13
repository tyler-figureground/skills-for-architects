# Programming

A Claude Code plugin for architectural space programming. Calculate IBC occupancy loads and build workplace space programs through guided conversation — from headcount and work style to area splits, room schedules, and seat counts, backed by industry research.

## The Problem

Space programming sits at the intersection of building code, workplace strategy, and client needs. Architects need to calculate occupancy loads from IBC tables, then translate vague client requirements ("we need space for 200 people, hybrid work") into a detailed room-by-room program with defensible ratios. This requires expertise in code compliance, workplace typologies, and the math to make it all add up to the available square footage.

## The Solution

Two conversational skills — one for code-driven occupancy calculation, one for strategy-driven workplace programming — that guide the designer through a structured process while handling the math, code lookups, and tradeoff analysis.

```
┌──────────────────────────────────────────────────────────────┐
│                    DESIGNER INPUT                            │
│                                                              │
│  "200 people, hybrid 3 days/wk, 45,000 RSF, tech company"   │
└──────────────────────────┬───────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
   ┌───────────────────┐     ┌───────────────────┐
   │    Occupancy       │     │    Workplace      │
   │    Calculator      │     │    Programmer     │
   │                    │     │                   │
   │  IBC Table 1004.5  │     │  Industry data:   │
   │  load factors      │     │  • Zone ratios    │
   │                    │     │  • Desk standards  │
   │  4 phases:         │     │  • Room standards  │
   │  Discover →        │     │  • Hybrid adj.    │
   │  Calculate →       │     │                   │
   │  Detail →          │     │  4 phases:        │
   │  Refine            │     │  Discover →       │
   │                    │     │  Synthesize →     │
   │  Outputs:          │     │  Detail →         │
   │  • Occupant load   │     │  Refine           │
   │  • Egress width    │     │                   │
   │  • Exit count      │     │  Outputs:         │
   │  • Plumbing count  │     │  • Area splits    │
   │                    │     │  • Room schedule   │
   │                    │     │  • Seat breakdown  │
   │                    │     │  • Support spaces  │
   └─────────┬─────────┘     └─────────┬─────────┘
             │                         │
             ▼                         ▼
   ┌───────────────────┐     ┌───────────────────┐
   │  occupancy.json   │     │   program.json    │
   │  + markdown report│     │  + markdown report│
   │                   │     │  + CSV export      │
   └───────────────────┘     └───────────────────┘
```

## Data Flow

### Occupancy Calculator

| Phase | What happens |
|-------|-------------|
| **Discover** | Conversational — learns about the building, use types, areas |
| **Calculate** | Breaks space into areas, assigns IBC load factors, sums occupant loads |
| **Detail** | Calculates egress width, required exits, plumbing fixture counts |
| **Refine** | Handles adjustments, what-ifs, mixed-use scenarios |

Applies IBC Table 1004.5 load factors. Handles gross vs net area, mixed occupancy, mezzanines, fixed seating, and NYC Building Code variants.

Outputs `occupancy.json` for state persistence and a markdown report.

### Workplace Programmer

| Phase | What happens |
|-------|-------------|
| **Discover** | Learns the organization — headcount, work style, culture, hybrid policy |
| **Synthesize** | Forms custom recommendation with area splits across 5 zones |
| **Detail** | Proposes seat breakdown, room schedule, and support spaces |
| **Refine** | Handles adjustments with tradeoff explanations |

Programs space across five zones:

| Zone | Typical range | What's in it |
|------|--------------|-------------|
| Work | 13-46% | Assigned desks, private offices, benching |
| Meeting | 12-25% | Conference rooms, huddles, phone booths |
| Common | 5-30% | Cafe, lounge, pantry, reception |
| Circulation | 27% (fixed) | Corridors, lobbies |
| BOH | 2-12% | IT, storage, copy/mail, facilities |

Outputs `program.json` for state persistence, a markdown report, and optional CSV export compatible with Procore, PlanGrid, and BIM 360.

### Pipeline

The `/space-program` command runs both skills in sequence — occupancy first (code compliance), then workplace programming (strategy), carrying forward the occupancy results to inform the program.

```
Building info → Occupancy Calculator → occupant loads, egress
                                              │
                                              ▼
                         Workplace Programmer → area splits, rooms, seats
```

## Skills

| Skill | Description |
|-------|-------------|
| [occupancy-calculator](skills/occupancy-calculator/) | IBC occupancy load calculator — per-area loads, gross vs net, egress requirements |
| [workplace-programmer](skills/workplace-programmer/) | Workplace strategy consultant — area splits, room schedules, seat counts backed by industry research |

## Commands

| Command | Description |
|---------|-------------|
| [space-program](commands/space-program.md) | Full space program — occupancy calculation followed by workplace programming |

## Install

```bash
claude install github:AlpacaLabsLLC/skills-for-architects/03-programming
```

## License

MIT
