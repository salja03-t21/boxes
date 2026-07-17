# BirdHouse Perch Clearance Design

## Outcome

BirdHouse users can keep either a dowel hole or an integrated ledge slot clear
of a resized opening. Automatic placement leaves a 10 mm gap. Manual placement
uses an explicit gap in millimetres.

## User interface

Add two shared BirdHouse arguments:

- `perch_clearance_mode`, with `auto` and `manual` choices;
- `perch_clearance`, the manual gap in millimetres.

The settings apply to every enabled opening and to the selected `perch_mode`.
They do not change opening placement, perch dimensions, ledge tab dimensions,
or perch projection.

## Geometry contract

Clearance is measured vertically from the bottom edge of the opening to the
nearest edge of the mount cutout:

- for a ledge, the top edge of the rectangular through-tab slot;
- for a dowel, the top edge of the circular hole.

Automatic mode returns 10 mm. Manual mode returns `perch_clearance` exactly.
Both mount renderers use the same clearance helper, which keeps their semantics
identical and avoids duplicating coordinate calculations.

The mount centre is therefore the opening bottom minus the clearance minus half
the mount height or diameter. If this would place any part of the mount outside
the wall, generation raises a clear `ValueError`; it must not silently clamp or
alter the requested clearance.

An opening shape of `none` continues to suppress its associated mount.

## Compatibility

Existing URLs and saved configurations remain valid because both arguments
have defaults. Automatic placement intentionally changes to the safer 10 mm
clearance for both perch modes.

## Verification

Tests will generate SVG through the BirdHouse backend route and verify:

- automatic ledge and dowel clearance is 10 mm;
- manual clearance is represented exactly for both mount types;
- changing opening height preserves the requested edge-to-edge clearance;
- the shared setting is applied on every enabled side;
- invalid clearances that move a mount outside its wall are rejected;
- all existing option-matrix closure, spacing, sheet-bound, and non-overlap
  invariants continue to pass.

Documentation will define the measurement and include an example.
