# CLI parity and the accessible fallback

Type: grilling
Status: open
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
