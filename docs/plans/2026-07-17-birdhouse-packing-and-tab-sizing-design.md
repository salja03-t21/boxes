# BirdHouse Packing and Tab Sizing Design

## Goal

Make laser-cut BirdHouse ledges structurally substantial and arrange every
BirdHouse cutout compactly on the generated sheet.

## Tab sizing

Ledge tabs remain material-thickness deep so they pass through the wall. Their
width becomes independently configurable:

- `auto` uses one third of the ledge width, bounded to leave shoulders on both
  sides and never smaller than two material thicknesses;
- `manual` uses an explicit millimetre width validated against the ledge width.

`perch_projection` remains a dowel-only setting. Laser-cut ledges use their
configured `perch_ledge_depth` as their outward projection.

## Packing

BirdHouse will collect all panel, roof, and ledge rectangles before drawing.
A deterministic shelf packer will place them left-to-right and begin a new row
when the next part exceeds `sheet_width`. The default is 600 mm, with an
explicit configurable width for smaller laser beds. The packing order remains
stable, while every part stays within the selected width with spacing between
parts.

## Verification

Tests will cover automatic and manual tab widths, invalid manual values, and
the packing bounds of a BirdHouse with all openings and ledges enabled. Rendered
SVGs will be checked for the expected compact multi-row layout.
