# Lock the Atlas visual world

Type: prototype
Status: open
Blocked by: -
Parent: ../map.md

## Question

Three visual worlds were built as real Textual renders, headless at 132x38, and
published for comparison:

https://claude.ai/code/artifact/4a9756ec-d166-44d0-b76d-ddd9979fbbc6

- **A - POCHE.** Solid is mass, void is space; the firm's name is the interface
  metaphor. Filled blocks for folders on disk, hatched void for folders the map
  expects and disk lacks. Five-row block wordmark, the plus cut in vermilion.
  Ink on near-black, one red. Seven header rows.
- **B - TITLE BLOCK.** Everything is line, nothing is fill. Double-rule box-drawing
  letterforms sharing strokes with the tree, a bordered DRIVE / MAP / PROJECTS /
  ATTENTION strip. Blueprint cyan on charcoal. Seven header rows, three of wordmark.
- **C - PAPER.** Inverted: bone ground, ink text, wordmark knocked out of a solid
  ink bar. Three header rows. Fights a dark terminal theme.

Resolve:

1. Which world ships.
2. The header footprint rule. A costs seven rows before the first project appears -
   a quarter of a thirty-row terminal. Proposed: full wordmark on first paint and
   when the terminal is tall, collapsing to a single identity line once work starts.
   Accept, reject, or replace.
3. The glyph vocabulary for folder state: present, absent, drifted, unfiled, empty.
   The prototypes propose fill weight (A, C) versus struck labels on standard
   branches (B). This is what a first-time user must read without a legend.
4. Whether the locked world becomes a written visual authority (DESIGN.md, or a
   token module) or stays as reference renders.

Prototype source: the throwaway renderer used for the artifact. Rebuild rather than
extend it if further variants are needed - it is not Atlas code and must not become
Atlas code.
