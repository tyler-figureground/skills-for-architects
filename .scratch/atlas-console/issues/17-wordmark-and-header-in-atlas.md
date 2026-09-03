# The wordmark and header, as Atlas code

Type: task
Status: open
Blocked by: 14
Parent: ../map.md

## Question

Ticket 02 settled what the header looks like and proved it renders. This ships it
into `tools/atlas` as real code, under test. The prototype renderer is throwaway
and must not be lifted.

Build:

- **Glyph table.** Capitals plus `+` and space, six pixel rows tall, five columns
  wide, two-column gaps. Only the characters `SOLID+VOID ATLAS` needs, unless a
  second drive name makes a wider set worth it.
- **Half-block compositor.** Packs pixel-row pairs into one character row as
  U+2580 with foreground as the top pixel and background as the bottom. This is the
  whole height saving; it needs its own test.
- **Extrusion.** Darkened offset copies composited behind the face, depth in pixel
  rows, so depth 2 costs one character row.
- **Ramp sampler.** Multi-stop interpolation, sampled per pixel row.
- **Three compositions** and the width rule that picks between them: full at
  >= 115 columns, compact at 82 - 114, bar below 82. Atlas already declares Textual
  horizontal breakpoints; this may or may not want to use them.

Verification, all of which must actually run:

- `uv run pytest` green, with new tests for the compositor, the ramp, the width
  rule, and each composition's exact column count.
- Headless Textual renders at 148x40, 104x34, and 80x24 confirming the right
  composition is chosen at each width.
- The mark is decorative, so it must not be announced as content. Decide what a
  screen reader gets, in line with ticket 10.

Blocked by ticket 14 only for the colour tokens the header shares with node kinds;
the geometry can start before that lands if it is kept separate.
