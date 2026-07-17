# BirdHouse Clean Geometry and Layout Implementation Plan

> **For Codex:** REQUIRED SKILLS: Use `executing-plans` for execution and `codex-serena-beads-workflow` for Serena + Beads workflow discipline.

**Goal:** Produce correct, compact BirdHouse SVGs for every opening and perch option, with no malformed polygons, unintended cut lines, overlaps, or spacing violations.

**Architecture:** Replace duplicated approximate bounds with shared geometry helpers and pack exact part rectangles using the repository's existing `rectpack` dependency with rotation enabled. Validate rendered paths directly and through the real `BServer.serve` HTTP route.

**Tech Stack:** Python 3.10+, Boxes.py drawing API, rectpack, svgpathtools, lxml, pytest.

---

## Workflow tracking

Serena is installed but currently configured for another repository, so use the
workflow's `rg`/targeted-file fallback for this branch. This repository has no
Beads database; do not initialize one solely for this corrective change. Mirror
progress in the session plan and keep commits scoped to the tasks below.

### Task 1: Specify valid perch geometry

**Files:**
- Modify: `boxes/generators/birdhouse.py`
- Create: `tests/test_birdhouse_geometry.py`

**Step 1: Write failing geometry tests**

Add helpers that render an SVG and extract physical path bounds. Specify that a
30 x 30 mm ledge with a 10 x 3 mm tab has a 30 x 33 mm bound and contains no
automatic closing segment longer than 30 mm.

```python
def test_ledge_polygon_closes_without_an_extra_cut_line() -> None:
    box = configured_birdhouse()
    borders = box.ledgeBorders(30, 30, 10)
    closed = box._closePolygon(borders.copy())
    assert max(closed[::2]) <= 30
    assert polygon_size(box, borders) == pytest.approx((30, 33))
```

**Step 2: Verify RED**

Run:

```bash
.venv/bin/pytest -q tests/test_birdhouse_geometry.py -k ledge_polygon
```

Expected: FAIL because `ledgeBorders` does not exist and the current polygon
contains a 60 mm closing segment.

**Step 3: Implement the canonical ledge border**

Add `ledgeBorders(width, depth, tab_width)` and use a final positive 90-degree
turn before the closing depth edge. Replace both duplicated inline polygon
lists with the helper.

**Step 4: Verify GREEN**

Run the focused command from Step 2. Expected: PASS.

**Step 5: Commit**

```bash
git add boxes/generators/birdhouse.py tests/test_birdhouse_geometry.py
git commit -m "fix: close BirdHouse perch outlines"
```

### Task 2: Specify opening/perch correspondence

**Files:**
- Modify: `tests/test_birdhouse_geometry.py`
- Modify: `boxes/generators/birdhouse.py` only if the tests expose a defect

**Step 1: Write failing matrix tests**

Cover zero through four enabled sides and all perch modes. Count opening paths
inside wall groups and separately labeled perch groups.

```python
@pytest.mark.parametrize("enabled", [(), ("front",), ("front", "back"), SIDES])
def test_perches_exist_only_for_enabled_openings(enabled) -> None:
    svg = render_birdhouse(enabled=enabled, perch_mode="ledge")
    assert perch_labels(svg) == {f"{side} perch" for side in enabled}
```

**Step 2: Verify RED**

Run the new test. Expected: FAIL initially because the current long labels and
testable part identity do not meet the contract.

**Step 3: Implement only the necessary correspondence/label changes**

Keep `openingDimensions(...)=None` as the single disabled-side rule. Shorten
separate ledge labels to `<side> perch` and ensure ledges are built exclusively
from the enabled-opening descriptor list.

**Step 4: Verify GREEN and commit**

```bash
.venv/bin/pytest -q tests/test_birdhouse_geometry.py -k perch
git add boxes/generators/birdhouse.py tests/test_birdhouse_geometry.py
git commit -m "test: enforce BirdHouse opening perch mapping"
```

### Task 3: Replace approximate packing

**Files:**
- Modify: `boxes/generators/birdhouse.py`
- Modify: `tests/test_birdhouse_geometry.py`

**Step 1: Write failing layout-invariant tests**

Parse the path union for each physical SVG group and assert that distinct part
bounding boxes are separated by at least the configured spacing and that their
total x-span does not exceed `sheet_width`. Include the supplied 140 x 120 x
160 mm, four-opening, 30 x 30 mm ledge case.

**Step 2: Verify RED**

```bash
.venv/bin/pytest -q tests/test_birdhouse_geometry.py -k 'overlap or spacing or sheet_width'
```

Expected: FAIL with the current underestimated gable, wall, roof, and ledge
bounds.

**Step 3: Add exact size helpers and part descriptors**

Create shared `sideSize`, `roofSize`, `rectangularWallSize`, and `ledgeSize`
helpers. Define a small immutable part descriptor with stable ID, dimensions,
and a render callback accepting a move/orientation string. Update `side` and
`roof` to consume their size helpers.

**Step 4: Pack with rectpack**

Use one `newPacker(rotation=True, pack_algo=MaxRectsBssf, bin_algo=PackingBin.Global)`
bin sized to `sheet_width` by the sum of padded part heights. Add configured
spacing to every rectangle, pack, and render at returned coordinates with
`move="rotated"` when the packed orientation is swapped. Raise `ValueError` if
any part remains unpacked.

**Step 5: Verify GREEN and commit**

```bash
.venv/bin/pytest -q tests/test_birdhouse_geometry.py
git add boxes/generators/birdhouse.py tests/test_birdhouse_geometry.py
git commit -m "fix: pack BirdHouse parts from exact bounds"
```

### Task 4: Exercise the backend API option matrix

**Files:**
- Modify: `tests/test_birdhouse_geometry.py`

**Step 1: Add a BServer HTTP harness**

Construct a WSGI environment for `/BirdHouse`, invoke `BServer.serve`, capture
status/headers/body, and parse the returned SVG. Parameterize representative
combinations of opening shape, enabled sides, perch mode, automatic/manual
ledge size, automatic/manual tab size, box dimensions, and sheet width.

**Step 2: Assert geometry invariants for every response**

Every case must return status 200 with SVG content and pass the same closure,
part-count, overlap, spacing, and sheet-bound checks as direct rendering.

**Step 3: Verify and commit**

```bash
.venv/bin/pytest -q tests/test_birdhouse_geometry.py -k backend
git add tests/test_birdhouse_geometry.py
git commit -m "test: validate BirdHouse backend SVG matrix"
```

### Task 5: Update examples and documentation

**Files:**
- Modify: `examples/BirdHouse.svg`
- Modify: `documentation/src/configurable-generators.rst`
- Modify: `docs/plans/2026-07-17-birdhouse-clean-layout-design.md` only for discovered durable constraints

**Step 1: Regenerate the canonical example**

Use the local generator with reproducible metadata and inspect the SVG visually.

**Step 2: Document packing and opening/perch behavior**

State that rotation is permitted, `none` disables both opening and perch, and
`sheet_width` bounds the physical cut layout.

**Step 3: Commit**

```bash
git add examples/BirdHouse.svg documentation/src/configurable-generators.rst
git commit -m "docs: describe clean BirdHouse packing"
```

### Task 6: Verify, review, release, and evaluate live output

**Files:**
- Verify all branch changes
- Later modify the homelab image pin in its own PR

**Step 1: Run focused and full verification**

```bash
.venv/bin/pytest -q tests/test_birdhouse_geometry.py
.venv/bin/pytest -q -n auto
SKIP=autoflake,rstcheck,pytest .venv/bin/pre-commit run --all-files
git diff --check fork/master...HEAD
```

**Step 2: Run risk-proportional Bouncer**

Use the repo plan, phase, base SHA, and automatic gates. Resolve any FAIL before
handoff.

**Step 3: Open and merge the application PR after checks pass**

Build the immutable amd64 image from merged `master` and record its digest.

**Step 4: Promote the image pin through a homelab PR and deploy Swarm**

Do not direct-push either repository's main branch.

**Step 5: Evaluate the real backend**

Run the SVG option matrix against `http://boxes.ciothoughts.net/BirdHouse`,
render representative outputs to PNG/PDF, and inspect them for clean outlines,
non-overlap, spacing, counts, and bounds before marking the goal complete.
