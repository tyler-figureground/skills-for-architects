# CLI parity and the accessible fallback

Type: grilling
Status: resolved
Blocked by: -
Parent: ../map.md

## Question

Atlas has maintained CLI parity for every capability so far - doctor, lint, new, add,
clean, conform, contacts, project edit - with `--json` as the agent interface. The
prior critique named CLI parity as the accessible fallback, because Textual's
screen-reader support is unresolved.

This effort adds capabilities that are natively spatial: a folder tree, a search
overlay, a dossier panel.

Resolve:

- Is CLI parity a rule for this effort, a default with named exceptions, or dropped?
- If it holds, what is the CLI form of a navigable tree - `atlas tree PROJECT` with
  a rendered outline and `--json`? Of search? Of the dossier?
- Do file-level tree actions need CLI equivalents before they ship, or after?
- Does `--json` stay the agent interface for the new surfaces, and does anything in
  this effort change that contract?
- What is the honest accessibility claim in the README once this ships? The current
  position - CLI is the accessible path - has to either hold or be restated.

This ticket sets a rule the implementation tickets inherit, so it is worth settling
early even though nothing blocks it.

## Resolution

Status: resolved
Date: 2026-09-04
Decision: `docs/adr/0008-cli-parity-is-owed-by-writes-and-facts-and-colour-never-carries-a-distinction-alone.md`
Vocabulary: `CONTEXT.md`, under Atlas Interface Contract

Grilled to a decision after slipping sessions 6, 7 and 8. Two facts found while
answering it changed what the ticket was asking.

### The accessibility justification had no owner

Every "CLI parity is the accessible fallback" line in this repo traces to one
synthetic persona in `.impeccable/critique/...app-py.md:76` and to Textual's
unresolved [#2425]. Not to a person waiting on Atlas. The operator profile settled
at charting is the principal daily and studio staff occasionally.

So parity is **kept and re-founded** on the reason that is actually true here:
agent automation. Which also has no current consumer - nothing under `plugins/`,
`agents/` or `rules/` shells out to Atlas, so `--json` has zero callers today.
That is recorded rather than glossed: the rule is a bet on near-future use.

### The colour problem was worse than the ticket described

Measured, not assumed:

- `_names_its_fault()` dropped the Filing State word at narrow width on the
  reasoning that "the glyph and its colour still carry it". Drifted, Misplaced and
  Loose **share one glyph and one colour by design** (ADR 0004: colour answers
  whose problem it is, not which). The word was the only separator, so three
  states rendered identically - to everyone, not only to a colour-blind operator.
- What was left was vermilion `#E2452A` against ochre `#D9A441`: **1.82:1**
  against each other, below the 3:1 non-text floor, on the red/green axis. Every
  token clears 4.5:1 against the ground. Nothing had ever tested a token against
  another token.
- The trigger fired at the wrong width - terminal width below `SPLIT_COLUMNS`
  (100). Below 100 the console is Single-Region and the tree owns nearly the whole
  terminal, so an 87-column terminal stripped labels while holding ~85 columns.
- The effort's own research had already ruled on it:
  `docs/research/atlas-tui-ux-evidence.md:91`, HIGH/Primary, *"avoid color-only
  status."* Accepted, deferred here, then contradicted by shipped code.

### What was decided

- **CLI is owed by every capability that writes, and every capability that
  produces a fact.** Navigation exempt. Discharged in the same session as the
  surface, either order, never a later ticket.
- **`atlas tree PROJECT [--json] [--depth N]`** is the tree's CLI form. `doctor`
  keeps its shape - it is drive-wide and cheap precisely because it is shallow.
- **Abbreviate, never drop.** `NAME`, `PLACE`, `LOOSE`, `UNMAPPED`, caps to match
  the project list's register.
- **`layout.ABBREVIATE_COLUMNS = 60`**, named and commented as the approximation
  it is, because the Tree Region's share of the terminal depends on Composition
  and no single number is right for both.
- **README states the negative first** and describes the CLI by what is true of
  it, not as an untested fallback.

### Built

- `FilingStyle.short`; `_fault_word()` replacing `_names_its_fault()`;
  `ABBREVIATE_COLUMNS`; `app.py` keying `narrow` on it.
- `test_no_two_filing_states_are_told_apart_by_colour_alone` asserts the invariant
  structurally at both widths rather than pinning a colour.
- 364 tests, up from 360. Rendered headless at 120 / 87 / 77 / 59 / 46 columns.

### One bug the render found and the tests did not, again

`node_label` returned early for a file, **before** the fault word was appended. So
a Loose file and an Unfiled file were the same hatch in two hues at *every* width,
not just at narrow - the exact defect this ticket exists to kill, sitting in the
half of the renderer the folder work never touched. A file has no disclosure
marker and no child count; it still says what is wrong with it.

Second session running that rendering the screen found something a green suite
did not.

### Owed, and tracked rather than folded in

- `conform --node` plus undo - inside [ticket 23](23-tree-write-keys.md), because
  ADR 0008 makes it that ticket's own obligation.
- [`atlas tree`](24-atlas-tree-cli.md) - ticket 22's retroactive debt, charted as
  its own ticket so it cannot be silently dropped inside another's commit.

### Not done

Load State labels do not abbreviate - `not opened yet` runs past the viewport at
46 columns and the row scrolls. Same principle as the Fault Word, different
vocabulary, and outside what was decided here. Noted in the map's fog.

[#2425]: https://github.com/Textualize/textual/issues/2425
