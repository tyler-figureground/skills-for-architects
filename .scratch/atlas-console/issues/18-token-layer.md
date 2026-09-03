# The token layer

Type: grilling
Status: open
Blocked by: 14
Parent: ../map.md

## Question

Graduated from the map's fog now that the visual world is settled.

Ticket 02 produced a working palette as prototype constants. Ticket 05 proved tree
nodes take no CSS at all - `render_label` is the only route - so whatever holds
these values must be readable from Python, not only from a Textual stylesheet.
Meanwhile `app.py` already carries a `MODAL_CSS` string and a `STATUS_STYLES` dict,
which are two token systems that do not know about each other.

Resolve:

- What is the layer? A Textual theme, a CSS variable block, a Python module of
  constants, or a Python module that also generates the CSS?
- How do the existing `MODAL_CSS` and `STATUS_STYLES` migrate onto it, and does
  anything in the modal CSS need to stop being a literal?
- Does it carry glyphs as well as colours? Ticket 14's node kinds each need a
  glyph and a colour, and keeping them apart invites drift.
- Does it support more than one theme? Option C - PAPER, a light ground - was
  rejected as the default, not proven impossible. Is a light theme a real future
  or explicitly never?
- Do the CLI's colours come from here too, or does the CLI stay uncoloured?
- How does a test assert a colour without hard-coding the hex in the test?

Ticket 02 recorded the prototype values. This ticket decides where they live and
is the last thing standing between the design and the implementation tickets.
