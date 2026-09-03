# Lock the Atlas visual world

Type: prototype
Status: claimed
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

## Progress

**World locked: A - POCHE.** Solid is mass, void is space; fill weight carries
folder state. The console body is settled and is not reopened by anything below.

**Wordmark reopened by the user:** retro-cyberpunk 3D extruded gradient lettering,
which the original A did not have. Five treatments built and published on the same
sheet:

https://claude.ai/code/artifact/4a9756ec-d166-44d0-b76d-ddd9979fbbc6

- H1 OUTRUN - yellow through orange, magenta, violet. Vertical ramp, depth 2.
- H2 CHROME - cyan, forced white specular row, steel, magenta, violet.
- H3 EMBER - bone-gold through amber into the console's own vermilion. The only
  treatment that adds no colour the console does not already mean something by.
- H4 SCANLINE - diagonal ramp, depth 3, alternate rows dimmed to 62%. 195 colours.
- H5 COMPACT - H1's ramp, but SOLID+VOID in the 3D face with ATLAS captioned
  beside it. 82 columns instead of 111.

Construction: 5x5 block glyphs, two-column gaps, extrusion composited as darkened
offset copies *behind* the face, gradient sampled per cell from a multi-stop ramp.
Full mark measures 111 columns by 7 rows; H5 measures 82.

Three questions still open, on the sheet:

1. Which treatment - and is a second colour system in the header acceptable, given
   vermilion, ochre, sage and steel already carry meaning in the console below?
2. Nine rows before the first project. Where does the header collapse?
3. Does the retro register stop at the wordmark, or does the whole console go
   further (scanline dimming on rows, glow on selection, neon rules)?

Ticket stays claimed until those three are answered. Prototype source is throwaway
and lives in the session scratchpad only - it is not Atlas code.
