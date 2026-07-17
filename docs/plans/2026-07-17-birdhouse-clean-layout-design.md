# BirdHouse Clean Geometry and Layout Design

## Goal

Generate clean BirdHouse SVGs for every opening and perch option: each physical
part has a valid outline, enabled openings and perches correspond exactly, and
all cutouts are compactly packed without overlaps or spacing violations.

## Confirmed defects

The supplied `BirdHouse.pdf` exposes two independent geometry defects:

- the ledge polygon's last turn is `-90` instead of `90`, leaving the outline
  open by 60 mm for a 30 mm ledge; automatic closure adds an unintended long
  cut line and doubles the measured height;
- the custom shelf packer uses approximate heights. For the reviewed 140 x 120
  x 160 mm configuration, it underestimates gable panels by about 39.6 mm,
  side panels by about 36.6 mm, roofs by 3 mm, and malformed ledges by 27 mm.

The opening/perch selection path already excludes a side whose opening shape
is `none`. The regression suite must make this contract explicit: four enabled
openings yield four perches; disabled openings yield neither a wall opening nor
a separate perch part.

## Geometry model

BirdHouse will use one canonical ledge-border helper for rendering and
measurement. The corrected border closes naturally around the configured
ledge depth and centered through-tab. A 30 x 30 mm ledge with 3 mm material and
a 10 mm tab therefore has a 30 x 33 mm bounding box and no automatic long
closure segment.

Every physical cutout will be represented by a descriptor containing a stable
name, exact width and height, and a render callback that accepts normal or
rotated placement. Panel and roof size helpers will share the same edge-spacing
calculations as their renderers; no approximate duplicate dimensions remain.

## Packing

Use the repository's existing `rectpack` dependency with deterministic
MaxRects best-short-side-fit packing. Add the configured spacing to each packed
rectangle, allow 90-degree rotation, and use a single bin whose width is
`sheet_width` and whose height is the sum of all part heights. Render each part
at the resulting coordinate and orientation. Stable part identifiers provide
deterministic output when dimensions tie.

If any cutout cannot fit the configured width in either orientation, rendering
fails with a clear `ValueError`. The SVG canvas may include Boxes.py metadata
and reference margins, but the union of physical cut paths must remain within
the configured packing width.

Perch labels will be shortened to `<side> perch` so annotation text fits small
ledge parts more reliably and does not obscure the layout.

## Verification

Geometry tests will parse real SVG path data with `svgpathtools` and validate a
matrix of opening shapes, enabled-side combinations, perch modes, automatic and
manual sizes, tab modes, dimensions, and sheet widths. Assertions cover:

- XML validity and successful rendering;
- enabled-opening and perch-part counts;
- naturally closed ledge geometry with no unexpected long closure segment;
- expected ledge bounding dimensions;
- non-overlapping physical-part bounding boxes;
- configured minimum spacing;
- physical cut geometry within `sheet_width`;
- deterministic output and useful 90-degree rotation.

The same representative matrix will be rendered through `BServer.serve`, the
actual backend HTTP path used by the container. After release, it will be run
against the LAN endpoint before the deployment is considered complete.
