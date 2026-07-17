# Partial-cover UniversalBox and configurable BirdHouse Implementation Plan

> **For Codex:** REQUIRED SKILLS: Use `executing-plans` for execution and `codex-serena-beads-workflow` for Serena + Beads workflow discipline.

**Goal:** Add configurable partial top covers to `UniversalBox` and independently configurable openings plus shared perch choices to `BirdHouse`.

**Architecture:** Extend the existing generator classes and retain their standard Boxes.py argument parser, rendering lifecycle, and SVG output. New helpers will isolate geometry decisions: a UniversalBox cover helper will calculate and render a keyed cover strip, while BirdHouse helpers will draw per-wall openings and shared per-opening perch geometry.

**Tech Stack:** Python 3.10+, Boxes.py geometry/rendering framework, pytest, lxml SVG validation.

---

## Tracking and baseline

This upstream repository has no Beads database (`bd info` reports none), so no
Beads issue is created. Serena is configured globally but is not exposed as a
callable tool in this session; use targeted source search and keep the changes
within the two generator files and focused tests.

### Task 1: Add focused render-test helpers

**Files:**
- Create: `tests/test_configurable_generators.py`
- Modify: `examples.yml` only if project convention requires durable SVG fixture examples

**Step 1: Write failing UniversalBox cover tests**

Create a helper that instantiates a generator, passes CLI-style arguments,
renders a reproducible SVG, and parses it with `lxml`. Add tests for:

- `cover_mode=none` preserving the no-cover path;
- blank/text cover modes at front and back;
- percent and millimetre depth modes;
- invalid/oversized cover values raising a clear `ValueError`.

**Step 2: Run test to verify it fails**

Run: `uv run --extra dev pytest -q tests/test_configurable_generators.py -k universal_cover`

Expected: FAIL because the new arguments are unknown.

**Step 3: Add failing BirdHouse tests**

Add render tests for independent front/back/left/right selection, all four
opening shapes, `none`/dowel/integrated-ledge perch modes, automatic/manual
ledge sizing, and invalid dimensions.

**Step 4: Run test to verify it fails**

Run: `uv run --extra dev pytest -q tests/test_configurable_generators.py -k birdhouse`

Expected: FAIL because the new arguments and geometry do not exist.

**Step 5: Commit**

```bash
git add tests/test_configurable_generators.py
git commit -m "test: specify configurable box generators"
```

### Task 2: Implement UniversalBox partial-cover options

**Files:**
- Modify: `boxes/generators/universalbox.py`
- Test: `tests/test_configurable_generators.py`

**Step 1: Add parser options**

Add explicit arguments with Boxes.py conventions:

- `cover_mode`: `none`, `blank`, `text`;
- `cover_position`: `front`, `back`;
- `cover_depth_mode`: `percent`, `mm`;
- `cover_depth`: float, default 33.3;
- `cover_label`: string.

**Step 2: Run the focused test to verify the intended initial failure**

Run: `uv run --extra dev pytest -q tests/test_configurable_generators.py -k universal_cover`

Expected: failure until cover geometry is emitted.

**Step 3: Implement cover calculation and keyed rendering**

Add small helpers to convert the selected depth to millimetres, validate it
against the usable depth, select front/back placement, and emit the cover panel
and its matching support geometry. Use existing edge/panel primitives and
preserve the exact previous `cover_mode=none` path.

**Step 4: Run the focused test to verify it passes**

Run: `uv run --extra dev pytest -q tests/test_configurable_generators.py -k universal_cover`

Expected: PASS.

**Step 5: Commit**

```bash
git add boxes/generators/universalbox.py tests/test_configurable_generators.py
git commit -m "feat: add UniversalBox partial cover strip"
```

### Task 3: Implement BirdHouse opening controls

**Files:**
- Modify: `boxes/generators/birdhouse.py`
- Test: `tests/test_configurable_generators.py`

**Step 1: Add per-side parser options**

For `front`, `back`, `left`, and `right`, add:

- `<side>_opening_shape`: `none`, `circle`, `rectangle`, `oval`;
- `<side>_opening_width` and `<side>_opening_height`.

Use the current centred placement as the sole positioning rule.

**Step 2: Implement a shape-rendering helper**

Replace the fixed `side_hole` callback with helpers that select the requested
shape and use the appropriate current drawing primitive. Validate each shape's
dimensions and call the helper only for the enabled wall.

**Step 3: Run focused tests**

Run: `uv run --extra dev pytest -q tests/test_configurable_generators.py -k birdhouse_opening`

Expected: PASS.

**Step 4: Commit**

```bash
git add boxes/generators/birdhouse.py tests/test_configurable_generators.py
git commit -m "feat: configure BirdHouse openings by side"
```

### Task 4: Implement shared BirdHouse perch options

**Files:**
- Modify: `boxes/generators/birdhouse.py`
- Test: `tests/test_configurable_generators.py`

**Step 1: Add shared perch parser options**

Add:

- `perch_mode`: `none`, `dowel`, `ledge`;
- `perch_size_mode`: `auto`, `manual`;
- `perch_diameter`, `perch_projection`;
- `perch_ledge_width`, `perch_ledge_depth`.

**Step 2: Implement perch geometry**

Render a matching dowel-hole/part or integrated ledge below every enabled
opening. In automatic mode derive ledge proportions from the opening and
material thickness; in manual mode validate supplied dimensions. Do not emit
perch geometry for disabled openings or `none` mode.

**Step 3: Run focused tests**

Run: `uv run --extra dev pytest -q tests/test_configurable_generators.py -k birdhouse_perch`

Expected: PASS.

**Step 4: Commit**

```bash
git add boxes/generators/birdhouse.py tests/test_configurable_generators.py
git commit -m "feat: add BirdHouse perch options"
```

### Task 5: Add documentation and verify the complete feature

**Files:**
- Modify: `documentation/src/generators.rst` if generator option documentation is indexed there
- Modify: `examples.yml` and `examples/*.svg` only for approved, stable example cases
- Modify: `docs/plans/2026-07-17-partial-cover-and-birdhouse-design.md` only if implementation requires a documented design adjustment

**Step 1: Document user-facing options**

Document the new option groups and a concise practical example for each
generator, preserving existing documentation structure.

**Step 2: Run focused and complete checks**

Run:

```bash
uv run --extra dev pytest -q tests/test_configurable_generators.py
uv run --extra dev pytest -q
git diff --check
```

Expected: all tests pass and no whitespace errors.

**Step 3: Run risk-proportional Bouncer**

Because this changes generator code and publishes a feature-ready branch, run
the applicable code/security/import/lint gates using the repository Bouncer
configuration. If the repository lacks one, initialize it first.

**Step 4: Commit**

```bash
git add documentation examples.yml examples docs/plans
git commit -m "docs: describe configurable box generator options"
```

## Verification notes

- Preserve generator class docstrings when possible: Boxes.py embeds them in
  SVG metadata, so changing one alters the default SVG fixture even when the
  generated geometry is unchanged.
- On 2026-07-17 the full regression suite passed with `205 passed, 9 skipped`.
- The Sphinx HTML build renders the added documentation page, but strict
  warning mode is not currently usable for this upstream tree because of
  pre-existing warnings, including missing generated `generators.inc` and
  unavailable `boxes.mounts`/`boxes.svgutil` autodoc modules.
