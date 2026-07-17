# Integrated Perch and Cover Tabs Implementation Plan

> **For Codex:** REQUIRED SKILLS: Use `executing-plans` for execution and `codex-serena-beads-workflow` for Serena + Beads workflow discipline.

**Goal:** Make BirdHouse ledges and UniversalBox partial covers self-locating with material-aware tabs and matching slots.

**Architecture:** BirdHouse opening callbacks will cut one slot in the wall whenever the shared laser-cut ledge option is active, while ledge rendering will create a matching, centered tab. UniversalBox will replace glue support rails with complementary tab and slot geometry using the generator's existing finger-joint settings. Existing disabled-feature paths will remain unchanged.

**Tech Stack:** Python, boxes.py geometry primitives, pytest, lxml SVG parsing.

---

### Task 1: Specify BirdHouse ledge tab/slot output

**Files:**
- Modify: `tests/test_configurable_generators.py`
- Modify: `boxes/generators/birdhouse.py:118-153`

**Step 1: Write the failing test**

Add a test that renders a BirdHouse with one enabled opening and
`--perch_mode=ledge`, then asserts that the SVG contains both the wall-slot
geometry and the ledge's centered tab geometry. Add a paired assertion that
`perch_mode=none` does not add that slot.

**Step 2: Run test to verify it fails**

Run: `/Users/jamessalmon/.config/superpowers/worktrees/boxes/partial-cover-birdhouse/.venv/bin/pytest -q tests/test_configurable_generators.py -k ledge_tab`

Expected: FAIL because current ledges are plain rectangles and no wall slot is
cut.

**Step 3: Write minimal implementation**

Add a `ledgeMount` callback helper that computes a centered, material-thickness
slot below an opening. Invoke it for `perch_mode=ledge`. Replace the plain
`rectangularWall` ledge part with a ledge outline whose wall-facing edge has
one centered tab of matching thickness.

**Step 4: Run test to verify it passes**

Run the focused test command from Step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add boxes/generators/birdhouse.py tests/test_configurable_generators.py
git commit -m "feat: add locating tabs to birdhouse ledges"
```

### Task 2: Specify UniversalBox cover tabs and wall slots

**Files:**
- Modify: `tests/test_configurable_generators.py`
- Modify: `boxes/generators/universalbox.py:59-95,122-164`

**Step 1: Write the failing test**

Add a test rendering a covered UniversalBox with `top_edge=e`. Assert that the
SVG contains the partial-cover tab/slot geometry and does not contain the two
legacy "partial cover support" rails.

**Step 2: Run test to verify it fails**

Run: `/Users/jamessalmon/.config/superpowers/worktrees/boxes/partial-cover-birdhouse/.venv/bin/pytest -q tests/test_configurable_generators.py -k cover_tabs`

Expected: FAIL because the current output still contains two support rails.

**Step 3: Write minimal implementation**

Add helpers that derive the partial-cover tab locations from the current
material thickness and finger-joint settings. Use callbacks on the left and
right wall panels to create matching upper-wall slots at the chosen cover end.
Render the cover with the corresponding attachment tabs and remove the support
rail parts. Preserve the existing label callback and feature-disabled path.

**Step 4: Run test to verify it passes**

Run the focused test command from Step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add boxes/generators/universalbox.py tests/test_configurable_generators.py
git commit -m "feat: tab partial universal box covers"
```

### Task 3: Clarify circular dimensions and documentation

**Files:**
- Modify: `boxes/generators/birdhouse.py:27-36`
- Modify: `documentation/src/configurable-generators.rst`
- Test: `tests/test_configurable_generators.py`

**Step 1: Write the failing test**

Render two otherwise-identical circular openings with different supplied
heights and assert reproducible SVG equality. This locks in width-as-diameter
behavior.

**Step 2: Run test to verify it fails**

Run: `/Users/jamessalmon/.config/superpowers/worktrees/boxes/partial-cover-birdhouse/.venv/bin/pytest -q tests/test_configurable_generators.py -k circle_height`

Expected: FAIL because no explicit behavioral regression test exists.

**Step 3: Write minimal implementation**

Update the circle-height CLI help and user guide to say that circle width is
its diameter and height is ignored. Do not change the existing geometry logic.

**Step 4: Run test to verify it passes**

Run the focused test command from Step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add boxes/generators/birdhouse.py documentation/src/configurable-generators.rst tests/test_configurable_generators.py
git commit -m "docs: clarify circular birdhouse opening dimensions"
```

### Task 4: Verify and publish the correction

**Files:**
- Verify: `tests/test_configurable_generators.py`
- Verify: full test suite and package documentation build

**Step 1: Run focused generator tests**

Run: `/Users/jamessalmon/.config/superpowers/worktrees/boxes/partial-cover-birdhouse/.venv/bin/pytest -q tests/test_configurable_generators.py`

Expected: PASS.

**Step 2: Run full regression suite**

Run: `/Users/jamessalmon/.config/superpowers/worktrees/boxes/partial-cover-birdhouse/.venv/bin/pytest -q`

Expected: PASS with any known skips reported.

**Step 3: Build documentation**

Run: `uv run --extra dev sphinx-build -b html documentation/src /tmp/boxes-integrated-tabs-docs`

Expected: successful build; compare warnings to the known baseline if present.

**Step 4: Run proportionate release review**

Run focused Bouncer gates for changed generator code and tests. If the known
runner initialization failure recurs, record it and preserve the manual test
evidence rather than silently treating it as a pass.

**Step 5: Publish through pull requests**

Push `fix/birdhouse-perch-tabs`, open a PR into the maintained fork's
`master`, merge after required checks, obtain the immutable Docker image digest,
then update and merge a separate homelab image-pin PR before deploying to
Swarm.
