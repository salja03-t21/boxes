# Partial-cover UniversalBox and configurable BirdHouse design

## Goal

Extend the existing `UniversalBox` and `BirdHouse` generators with first-class,
laser-cuttable storage and birdhouse options while preserving their current
output when the new options are disabled.

## Decisions

### UniversalBox partial top cover

`UniversalBox` will gain an optional fixed strip across one end of an otherwise
open top. The strip covers the full inside width and a configurable portion of
the depth. It provides a grip boundary and a top-facing label area.

- Cover mode: `none`, `blank`, or `text`.
- Cover position: `front` or `back`.
- Cover depth mode: percentage of the usable box depth or explicit millimetres.
- Cover depth value: default 33.3 percent.
- Label text: engraved only in `text` mode.
- The strip is a keyed box component, with matching support/slot geometry on
  the affected walls; it is not a loose, manually aligned rectangle.
- Existing `UniversalBox` output remains unchanged for cover mode `none`.

### BirdHouse openings and perch

`BirdHouse` will gain independent opening controls for front, back, left, and
right panels.

- Per side, shape is `none`, `circle`, `rectangle`, or `oval`.
- Per side, dimensions are independent. Circle uses diameter; rectangle and
  oval use width and height.
- Openings remain centred on their wall.
- One shared perch setting applies beneath every enabled opening: `none`,
  `dowel`, or `integrated ledge`.
- Dowel diameter and projection are explicit millimetre values.
- Integrated ledge dimensions use either automatic proportions derived from
  the opening/material, or explicit dimensions.
- Decorative/styled opening profiles are deliberately deferred.

## Implementation approach

Modify the existing generators rather than introduce near-duplicate variants.
This preserves their UI routes, generated links, conventional Boxes.py
arguments, existing edge settings, and user expectations.

The UniversalBox cover is implemented as a panel plus keyed supporting
geometry in the relevant wall render paths. BirdHouse receives small,
well-named callback helpers to draw each shape and optionally emit the shared
perch parts. Existing geometry helpers (`rectangularHole`, circle/oval drawing,
and `rectangularWall`) remain the rendering primitives.

## Validation

Tests will render generator SVGs and assert the new geometry/metadata contract.
They cover default compatibility, both cover positions and depth modes,
engraved versus blank cover behavior, each BirdHouse side and opening shape,
all perch modes, and invalid values. The full existing SVG suite will run
before handoff.

## Out of scope

- Arbitrary custom opening paths or decorative profiles.
- Per-opening perch style/dimensions.
- An external label-template or label-printer integration.
