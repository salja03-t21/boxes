# Integrated Perch and Cover Tabs Design

## Context

The first configurable-generator release added BirdHouse laser-cut ledges as
separate rectangular parts and UniversalBox partial covers as separate panels
with glue support rails. Neither part had a positive mechanical location. This
made assembly less repeatable and did not meet the expectation that both
features use the box generator's normal tab-and-slot construction.

## Goals

- Give every laser-cut BirdHouse ledge a centered, through-wall locating tab
  and a matching slot directly below its opening.
- Make each optional UniversalBox partial cover integrate with matching tabs
  and slots rather than glue-only support rails.
- Preserve the default output when either optional feature is disabled.
- State clearly that a circular birdhouse opening uses width as its diameter;
  its height option is not applicable.

## Design

### BirdHouse laser-cut ledges

Each generated ledge has a single centered tab along its wall-facing edge. The
tab is material-thickness wide and passes through one matching rectangular slot
in the selected wall. The tab is placed below the opening with the ledge
centered horizontally, producing a self-locating 90-degree shelf. Glue remains
recommended for final strength; the tab is for location and squareness.

The existing `perch_mode=dowel` behavior is unchanged. Opening callbacks own
the matching wall slots, so a slot is made only for a side whose opening exists
and whose shared perch mode is `ledge`.

### UniversalBox partial cover

The partial cover replaces its two glue support rails with finger-joint tabs
along the cover's left and right attachment edges. The upper sections of the
matching box side walls receive the complementary slots. The generator reuses
the current finger-joint settings rather than adding separate tab controls, so
cover joints match the configured box construction.

Because the cover is a separate symmetric part, `cover_position` continues to
identify its assembly location (front or back), while the tab geometry makes
that location mechanically repeatable.

### Circle dimensions

A circle is defined by a single diameter. For `*_opening_shape=circle`, the
corresponding `*_opening_width` value is the diameter and
`*_opening_height` is ignored. This is described in the UI help and user
documentation; rectangle and oval openings continue to use both measurements.

## Verification

Tests will first demonstrate the absence of tab/slot geometry. The correction
will then test generated SVG geometry for ledge tabs and wall slots, and for
the UniversalBox cover's finger-joint integration. Existing default-output
tests will remain unchanged. Focused generator tests, the full test suite, and
the immutable Docker image workflow will be required before promotion.
