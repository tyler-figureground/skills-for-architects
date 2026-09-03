# Dossier panel

Type: grilling
Status: open
Blocked by: 03
Parent: ../map.md

## Question

Reading `PROJECT.md` inside Atlas is in scope. The dossier already has a machine
contract - ADR 0001 covers its shared front matter, `core/projectmd.py` reads and
writes it, and `core/project_data.py` exposes `load_project_record`.

Resolve, once the layout model is fixed:

- Which facts surface: identity, site address, use case, billing and client contact
  snapshots, decisions index, code edition. All of them, or a chosen subset?
- Read-only, or editable in place? Atlas already has a full edit path behind `e`
  with rename preview and confirmation - does the dossier panel duplicate an entry
  point into that, or become a second way to write?
- Where does it live in the layout model ticket 03 settles: a pane, a mode of the
  right pane, or a full-screen view?
- What renders when `PROJECT.md` is missing, malformed, or legacy? Core deliberately
  refuses to silently rewrite malformed dossier data - the panel must say so
  usefully rather than showing blanks.
- Does the decisions index link through to `decisions/NNNN-slug.md`, and can those
  be read in Atlas too, or is that a different surface?
- Is there a CLI equivalent, or is `cat PROJECT.md` the answer?
