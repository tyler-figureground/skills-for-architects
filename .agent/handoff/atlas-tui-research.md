# Atlas TUI research continuity

## Objective
Research current primary-source evidence for improving Atlas, a small Python Textual terminal UI for architecture studio project folders.

## Constraints
- Do not expose repository code externally.
- Prefer official docs, API references, source, release notes, and first-party issue trackers.
- Include confidence tiers, direct URLs, contradictions/hidden variables, negative evidence, survivorship-bias sweep, don't-hand-roll guidance, and prioritized implementation shortlist.

## Phases
- [x] Fetch remote and survey repository state.
- [x] Inspect Atlas locally for scope and current interaction model.
- [x] Gather Textual primary evidence by requested topic.
- [x] Gather exemplary TUI primary evidence (lazygit, k9s, Yazi, VisiData).
- [x] Search migration, regression, and abandoned-approach evidence.
- [x] Synthesize report under `docs/research/`.
- [x] Verify links, structure, repository lint, and working-tree diff.

## Repository state at start
- Branch `main`, ahead 0 / behind 0 after `git fetch --all --prune`.
- Pre-existing modified files present, including Atlas files. Do not overwrite or revert them.

## Result
- Evidence report: `docs/research/atlas-tui-ux-evidence.md`
- UX critique: 20/40 - acceptable foundation, significant operational UX work needed.
- Baseline verification: repo lint passed; Atlas tests 44 passed; detector found 0 mechanical issues.
- Implementation approved. Direction: expert operations console.
- Recommended first slice: non-blocking scan, stable keyed rows, responsive project-health detail, contextual actions/help, durable result/error state.

## Implementation phases
- [x] Phase 1 - pure project-table view model and studio-language details.
- [x] Phase 2 - responsive operations-console layout, filtering, sorting, help, contextual actions.
- [x] Phase 3 - threaded scans/mutations, durable results, retry and error containment.
- [x] Phase 4 - empty, narrow, keyboard, failure, and operation-result tests.
- [x] Phase 5 - lint, tests, detector, rendered TUI verification, final review.

## Final verification
- `cd tools/atlas && uv run pytest -q` - 69 passed.
- `cd tools/atlas && uv build` - wheel and source distribution built.
- `./scripts/lint.sh` - passed; shellcheck unavailable locally and skipped by script.
- Impeccable layout detector - 0 findings.
- Textual headless renders verified at 130x36 and 80x24.
- Three safety review loops completed; findings resolved through stale-plan fingerprints, root-safe directory creation, exclusive control-file creation, and batch partial-result accounting.

## Synthetic safe-drive smoke
- Created and automatically removed a temporary 120-project drive. No production/shared drive touched.
- Mix: 64 conform, 40 drift, 16 unfiled projects.
- Core scan, full report, JSON doctor/lint, 130x36 TUI mount, and filter-to-one-project flow passed.
- Warm local timings varied by cache: scan ~16 ms, report ~186 ms, CLI doctor+lint ~68 ms, TUI mount ~599 ms. These are local filesystem baselines, not Google Drive latency claims.
