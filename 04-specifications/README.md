# Specifications

A Claude Code plugin for construction documentation. Generate CSI MasterFormat outline specifications from a materials list, and create structured punch lists from field notes and photos — organized by trade, priority, and CSI division.

## The Problem

Specification writing is tedious and repetitive — mapping materials to CSI divisions, writing three-part specs with the right language, referencing standards. Punch lists are worse — scribbled field notes and phone photos need to be organized by trade, location, priority, and division before they're useful to a contractor.

## The Solution

Two skills that handle the structured documentation work. The spec writer knows CSI MasterFormat 2020 and produces properly formatted outline specs. The punch list generator reads field notes and photos, categorizes items by trade and priority, and flags code/safety issues automatically.

```
┌──────────────────────────────────────────────────────────────┐
│                     DESIGNER INPUT                           │
│                                                              │
│  Materials list       OR       Field notes + photos          │
│  "porcelain tile,              "ceiling tile stained in      │
│   steel studs,                  conf. room B, paint touch-up │
│   gypsum board..."              needed at door 204..."       │
└─────────────┬────────────────────────────┬───────────────────┘
              │                            │
              ▼                            ▼
   ┌───────────────────┐        ┌───────────────────┐
   │   Spec Writer     │        │  Redline Punch    │
   │                   │        │  List Generator   │
   │  Materials →      │        │                   │
   │  CSI divisions →  │        │  Notes/photos →   │
   │  3-part specs     │        │  categorize →     │
   │                   │        │  prioritize →     │
   │  Divisions:       │        │  flag safety      │
   │  03-26             │        │                   │
   │  (Concrete →      │        │  By location,     │
   │   Electrical)     │        │  trade, division, │
   │                   │        │  priority          │
   │  Part 1: General  │        │                   │
   │  Part 2: Products │        │  Auto-flags:      │
   │  Part 3: Execution│        │  Exit signs,      │
   │                   │        │  ADA clearances,  │
   │  [REVIEW REQUIRED]│        │  fire-rated,      │
   │  flags on generic │        │  handrails,       │
   │  or safety specs  │        │  tripping hazards │
   └─────────┬─────────┘        └─────────┬─────────┘
             │                            │
             ▼                            ▼
   ┌───────────────────┐        ┌───────────────────┐
   │  Markdown file    │        │  Markdown file    │
   │  outline-specs-   │        │  punch-list-      │
   │  [project].md     │        │  [project].md     │
   │                   │        │  + optional CSV   │
   │                   │        │  (Procore/PlanGrid│
   │                   │        │   compatible)     │
   └───────────────────┘        └───────────────────┘
```

## Data Flow

### Spec Writer

| Step | What happens |
|------|-------------|
| **Parse** | Reads materials list (pasted, file, or verbal) and classifies into CSI divisions |
| **Generate** | Writes 3-part outline specs — General, Products, Execution — with standards references |
| **Annotate** | Adds `[REVIEW REQUIRED]` flags on generic specs, life-safety sections, assumed criteria |
| **Export** | Saves markdown file |

Covers 11 CSI MasterFormat 2020 divisions (03 Concrete through 26 Electrical). Uses proper spec language — "shall", "provide", "verify", imperative mood, no contractions.

### Redline Punch List

| Step | What happens |
|------|-------------|
| **Parse** | Reads field notes, photos, or guided walkthrough input |
| **Categorize** | Assigns location, CSI division, trade, priority (Critical/Major/Minor) |
| **Flag** | Automatically marks code/safety issues as Critical — exit signs, egress, ADA, fire-rated assemblies, exposed wiring |
| **Export** | Saves markdown with summary stats + optional CSV for Procore/PlanGrid/BIM 360 |

Supports substantial completion, final, warranty, and pre-occupancy inspection phases. Photos are read visually and described.

## Skills

| Skill | Description |
|-------|-------------|
| [spec-writer](skills/spec-writer/) | CSI outline specification writer — maps materials to MasterFormat 2020 divisions with three-part specs |
| [redline-punch-list](skills/redline-punch-list/) | Construction punch list generator — field notes and photos into structured lists by trade, priority, and CSI division |

## Install

```bash
claude install github:AlpacaLabsLLC/skills-for-architects/04-specifications
```

## License

MIT
