# Presentations

A Claude Code plugin for visual communication. Generate self-contained HTML slide decks, create harmonious color palettes, and batch-resize images for web, social, slides, and print — all from a single command.

## The Problem

Architects and designers spend hours on visual production work — fighting PowerPoint layouts, selecting colors without systematic contrast checks, and manually resizing the same image six times for different deliverables. All of it takes time away from design thinking.

## The Solution

Three skills that handle visual production. The slide deck generator builds complete HTML presentations from a topic or outline. The color palette generator creates systematic palettes with WCAG contrast checks from any starting point. The image resizer batch-exports project photos to every required format — web, social, slides, and print — in one step.


## Data Flow

### Slide Deck Generator

| Step | What happens |
|------|-------------|
| **Understand** | Reads input — topic, outline, document, or data |
| **Plan** | Selects slide types, plans narrative arc, decides count |
| **Build** | Writes self-contained HTML with CSS, navigation, and responsive typography |
| **Save** | Single `.html` file, no dependencies |

22 slide types cover titles, text, statistics, data tables, bar charts, timelines, comparisons, image grids, and full-bleed images. Every deck follows composition rules — alternate backgrounds, limit dark slides to 1-2, headlines state insights not topics.

### Color Palette Generator

| Step | What happens |
|------|-------------|
| **Interpret** | Reads input — text description, image, brand reference, or single color |
| **Generate** | Creates 8-12 colors in four groups with harmony rules (analogous, complementary, triadic) |
| **Validate** | Checks WCAG AA contrast ratios for all pairings, flags failures |
| **Export** | Self-contained HTML file that uses its own palette for styling |

Considers warm/cool balance, dominant/supporting/accent proportions, and tinted neutrals (never pure `#FFFFFF`).

## Skills

| Skill | Description |
|-------|-------------|
| [slide-deck-generator](skills/slide-deck-generator/) | Self-contained HTML slide decks with 22 slide types and an editorial design system |
| [color-palette-generator](skills/color-palette-generator/) | Harmonious color palettes from descriptions, images, or brand references with WCAG contrast checks |
| [resize-images](skills/resize-images/) | Batch-resize photos for web (WebP), social (center-cropped), slides (4:3 and 16:9), and print (ARCH A/B/C at 300 DPI) |

## Install

**Claude Desktop:**

1. Open the **+** menu → **Add marketplace from GitHub**
2. Enter `AlpacaLabsLLC/skills-for-architects`
3. Install the **Presentations** plugin

**Claude Code (terminal):**

```bash
claude plugin marketplace add AlpacaLabsLLC/skills-for-architects
claude plugin install 07-presentations@skills-for-architects
```

**Manual:**

```bash
git clone https://github.com/AlpacaLabsLLC/skills-for-architects.git
ln -s $(pwd)/skills-for-architects/plugins/07-presentations/skills/slide-deck-generator ~/.claude/skills/slide-deck-generator
ln -s $(pwd)/skills-for-architects/plugins/07-presentations/skills/color-palette-generator ~/.claude/skills/color-palette-generator
ln -s $(pwd)/skills-for-architects/plugins/07-presentations/skills/resize-images ~/.claude/skills/resize-images
```

## License

MIT
