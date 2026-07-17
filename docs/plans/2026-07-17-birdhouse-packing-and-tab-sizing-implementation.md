# BirdHouse Packing and Tab Sizing Implementation Plan

> **For Codex:** REQUIRED SKILLS: Use `executing-plans` for execution and `codex-serena-beads-workflow` for Serena + Beads workflow discipline.

**Goal:** Add proportionate/manual ledge tabs and deterministic sheet-width packing for every BirdHouse cutout.

**Architecture:** Extract BirdHouse parts into render callbacks with known dimensions, then place them through a shelf-layout helper. Keep the existing geometry helpers and extend them with validated tab dimensions.

**Tech Stack:** Python, boxes.py SVG geometry, pytest.

---

### Task 1: Specify tab dimensions

**Files:** `boxes/generators/birdhouse.py`, `tests/test_configurable_generators.py`

1. Add failing tests for automatic one-third tab width and manual override.
2. Run focused tests and observe failure.
3. Add tab-width arguments, validation, and `ledgeTabWidth` helper.
4. Rerun focused tests and commit.

### Task 2: Pack all BirdHouse cutouts

**Files:** `boxes/generators/birdhouse.py`, `tests/test_configurable_generators.py`

1. Add a failing test for a full BirdHouse layout bounded by `sheet_width`.
2. Run it and observe failure.
3. Add stable shelf placement for all panels, roofs, and ledges.
4. Rerun focused and full generator tests and commit.

### Task 3: Document and release

**Files:** `documentation/src/configurable-generators.rst`, `tests/test_configurable_generators.py`

1. Document tab sizing and sheet width.
2. Run full tests and documentation build.
3. Publish application and homelab PRs, deploy the immutable image, and verify live SVG bounds.
