# BirdHouse Perch Clearance Implementation Plan

> **For Codex:** REQUIRED SKILLS: Use `executing-plans` for execution and `codex-serena-beads-workflow` for Serena + Beads workflow discipline.

**Goal:** Add shared automatic or manual opening-to-perch clearance for both BirdHouse dowel holes and integrated ledge slots.

**Architecture:** Add one clearance resolver and one mount-centre calculation to `BirdHouse`, then route both perch mount renderers through them. Preserve the existing shared-perch model while making automatic clearance 10 mm and rejecting coordinates outside the wall instead of clamping them.

**Tech Stack:** Python, Boxes.py geometry callbacks, pytest, lxml, svgpathtools, WSGI `BServer.serve` backend harness.

**Workflow note:** Serena is configured for another repository and this repository has no Beads database. Use targeted `rg`/symbol inspection and the session `update_plan` fallback; do not initialize new repository metadata for this change.

---

### Task 1: Define the clearance geometry contract

**Files:**
- Modify: `tests/test_birdhouse_geometry.py:150-185`
- Modify: `boxes/generators/birdhouse.py:61-90,191-206`

**Step 1: Write failing unit tests**

Add tests that parse default, automatic, and manual settings and exercise the shared centre calculation:

```python
@pytest.mark.parametrize(
    ("mode", "configured", "expected"),
    [("auto", 3, 10), ("manual", 17, 17)],
)
def test_perch_clearance(mode: str, configured: float, expected: float) -> None:
    box = BirdHouse()
    box.parseArgs([
        f"--perch_clearance_mode={mode}",
        f"--perch_clearance={configured}",
    ])
    assert box.perchClearance() == expected


def test_perch_mount_position_uses_edge_to_edge_clearance() -> None:
    box = BirdHouse()
    box.parseArgs(["--perch_clearance_mode=manual", "--perch_clearance=17"])
    assert box.perchMountY(80, 40, 8) == 39
```

Also test that a negative manual clearance and a clearance that pushes the
mount below the wall raise `ValueError` with useful messages.

**Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest -q tests/test_birdhouse_geometry.py -k 'perch_clearance or perch_mount_position'`

Expected: FAIL because the arguments and helpers do not exist.

**Step 3: Add arguments and shared helpers**

In `BirdHouse.__init__`, add:

```python
self.argparser.add_argument(
    "--perch_clearance_mode", action="store", type=str,
    choices=("auto", "manual"), default="auto",
    help="place perch mounts with automatic or manual opening clearance")
self.argparser.add_argument(
    "--perch_clearance", action="store", type=float, default=10.0,
    help="manual gap between the opening and perch mount")
```

Add shared helpers:

```python
def perchClearance(self):
    clearance = 10.0 if self.perch_clearance_mode == "auto" else self.perch_clearance
    if clearance < 0:
        raise ValueError("perch clearance must not be negative")
    return clearance

def perchMountY(self, opening_y, opening_height, mount_height):
    mount_y = (
        opening_y - opening_height / 2
        - self.perchClearance() - mount_height / 2
    )
    if mount_y - mount_height / 2 < 0:
        raise ValueError("perch clearance places the mount outside the wall")
    return mount_y
```

Replace both existing `max(...)` calculations with `perchMountY(...)`, using
`perch_diameter` for the dowel and material thickness for the ledge slot.

**Step 4: Run focused tests**

Run: `.venv/bin/pytest -q tests/test_birdhouse_geometry.py -k 'perch_clearance or perch_mount_position'`

Expected: all selected tests PASS.

**Step 5: Commit**

```bash
git add boxes/generators/birdhouse.py tests/test_birdhouse_geometry.py
git commit -m "feat: configure BirdHouse perch clearance"
```

### Task 2: Verify rendered backend geometry

**Files:**
- Modify: `tests/test_birdhouse_geometry.py:38-130,186-249`

**Step 1: Add a cutout-gap extractor**

Add a helper that finds the group containing one uniquely sized opening and its
smaller blue mount path. Normalize for 90-degree packed rotation, then return
the non-overlapping axis gap between their bounding boxes.

```python
def rendered_mount_gap(svg: bytes, opening_size: float) -> float:
    # Find a group with the requested opening and exactly one perch mount.
    # Return the positive x- or y-axis edge separation.
    ...
```

**Step 2: Write failing backend tests**

Generate a front-only circular opening through `backend_render_birdhouse` for
both `dowel` and `ledge`, and for both placement modes:

```python
@pytest.mark.parametrize("perch_mode", ["dowel", "ledge"])
@pytest.mark.parametrize(
    ("clearance_mode", "clearance", "expected"),
    [("auto", 2, 10.2), ("manual", 17, 17.2)],
)
def test_backend_renders_requested_perch_clearance(...):
    svg = backend_render_birdhouse({...})
    assert rendered_mount_gap(svg, opening_size=32) == pytest.approx(expected)
```

The extra 0.2 mm is the two inward 0.1 mm burn offsets on the measured SVG cut
edges. Add a second opening height case to prove the edge gap remains constant.

Add backend error tests for negative clearance and a value that cannot fit below
the opening. Adjust the WSGI helper only as needed to expose the non-200 error
without weakening existing success assertions.

**Step 3: Run tests to verify expected failures**

Run: `.venv/bin/pytest -q tests/test_birdhouse_geometry.py -k 'backend_renders_requested_perch_clearance or clearance_error'`

Expected: FAIL until both mount renderers use the shared calculation and the
test helper correctly identifies their SVG paths.

**Step 4: Complete the SVG helper and matrix coverage**

Add `perch_clearance_mode` and representative clearance values to the existing
64-case backend matrix. Preserve all closure, opening count, part count, label,
spacing, sheet-width, and non-overlap assertions.

**Step 5: Run BirdHouse tests**

Run: `.venv/bin/pytest -q tests/test_birdhouse_geometry.py`

Expected: all BirdHouse geometry and backend cases PASS.

**Step 6: Commit**

```bash
git add tests/test_birdhouse_geometry.py boxes/generators/birdhouse.py
git commit -m "test: verify BirdHouse perch clearance SVGs"
```

### Task 3: Document and refresh the example

**Files:**
- Modify: `documentation/src/configurable-generators.rst:35-61`
- Modify: `examples/BirdHouse.svg`

**Step 1: Update user documentation**

Document that `perch_clearance_mode=auto` leaves 10 mm between the opening and
the nearest mount edge. Document manual mode, the exact edge-to-edge
measurement, shared-side behavior, both perch types, and invalid wall-boundary
errors. Include a concise 17 mm example.

**Step 2: Regenerate the canonical SVG**

Use the same reproducible generator path used by the fixture test so
`examples/BirdHouse.svg` reflects the new safe automatic placement.

**Step 3: Verify docs and fixture**

Run: `.venv/bin/pytest -q tests/test_configurable_generators.py tests/test_birdhouse_geometry.py`

Expected: all selected tests PASS, including the canonical SVG fixture.

**Step 4: Commit**

```bash
git add documentation/src/configurable-generators.rst examples/BirdHouse.svg
git commit -m "docs: explain BirdHouse perch clearance"
```

### Task 4: Release verification

**Files:**
- Verify: all changed files

**Step 1: Run formatting and static checks**

Run: `git diff --check`

Run: `SKIP=autoflake,rstcheck,pytest .venv/bin/pre-commit run --all-files`

Expected: all selected hooks PASS.

**Step 2: Run the full suite**

Run: `.venv/bin/pytest -q`

Expected: 0 failures.

**Step 3: Run risk-proportional Bouncer**

Run:

```bash
~/.codex/bin/bouncer \
  --plan-file docs/plans/2026-07-17-birdhouse-perch-clearance.md \
  --phase "BirdHouse perch clearance" \
  --base-sha a06fb4d0e96ab8817cce896d3091e2992450e790 \
  --working-dir "$PWD" --gates auto --json
```

Expected: PASS for the behavior, focused tests/coverage, lint, and full suite
gates. Fix and rerun any blocking finding.

**Step 4: Inspect representative SVGs**

Render automatic and 17 mm manual examples for both perch modes. Inspect the
SVG path geometry and raster previews for correct gap, closed shapes, wall
bounds, and non-overlap.

**Step 5: Commit any verification-driven corrections**

Commit only if verification required a source, test, docs, or fixture change.

### Task 5: Promote and deploy

**Files:**
- Application PR: `salja03-t21/boxes`, target `master`
- Deployment pin: `docker_swarm/boxes/compose.yml` in `salja03-t21/homelab`
- Deployment contract: `scripts/tests/test_boxes_stack.py`
- Service documentation: `docs/services/boxes.md`

**Step 1: Push and open an application PR**

Push `feat/birdhouse-perch-clearance`, open a PR to fork `master`, and wait for
the Docker plus Python 3.10/3.14 checks. Merge only when all required checks
pass.

**Step 2: Wait for and inspect the signed image**

Record the immutable `sha-<merge>` tag and OCI index digest. Confirm the index
contains the reviewed `linux/amd64` manifest and signing attestation.

**Step 3: Update homelab through a separate PR**

In an isolated homelab worktree from `origin/main`, update the exact image tag
and digest in the stack, contract test, and service release note. Run the stack
contract and Docker Compose render, then merge by PR.

**Step 4: Deploy the merged homelab snapshot**

Archive `origin/main` to `/home/james/homelab`, deploy the `boxes` stack, and
wait for `boxes_boxes` to run healthy on the exact digest.

**Step 5: Verify the live LAN backend**

Run automatic and manual clearance cases for both perch modes through
`http://boxes.ciothoughts.net/BirdHouse`. Parse the returned SVGs and verify the
same clearance, path closure, spacing, bounds, and non-overlap invariants used
locally.
