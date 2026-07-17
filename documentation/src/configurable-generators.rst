Configurable storage and birdhouse features
===========================================

UniversalBox partial cover
--------------------------

UniversalBox can add a fixed strip across the front or back of an open top.
Set ``top_edge`` to ``e`` and choose one of these cover modes:

* ``none`` keeps the original open box;
* ``blank`` generates an unmarked cover strip;
* ``text`` engraves ``cover_label`` on the strip.

``cover_depth_mode`` accepts ``percent`` (the default) or ``mm``. With percent,
``cover_depth`` is the percentage of box depth; with mm it is an absolute
millimetre dimension. The default is 33.3 percent. ``cover_position`` chooses
``front`` or ``back``.

The cover uses the generator's finger-joint settings along its two side edges.
Matching finger slots are cut into the upper sections of both side walls at the
selected end, making the cover self-locating. Glue the fitted joints for final
strength.

BirdHouse openings and perches
------------------------------

BirdHouse exposes opening controls for ``front``, ``back``, ``left``, and
``right`` independently. For each side select ``<side>_opening_shape`` as
``none``, ``circle``, ``rectangle``, or ``oval``. Use the matching width and
height fields to set the size; circles use width as their diameter and ignore
the corresponding height field. A zero dimension preserves the original
automatic proportion for a rectangular opening. Openings remain centred on
their wall.

``perch_mode`` applies the same choice below every enabled opening:

* ``none`` adds no perch;
* ``dowel`` cuts a mounting hole using ``perch_diameter``. Supply a dowel and
  install it with the desired ``perch_projection``;
* ``ledge`` adds one laser-cut ledge panel for each enabled opening.

An opening shape of ``none`` disables both the wall opening and its associated
perch. Separate ledge parts are generated only when ``perch_mode=ledge``;
``none`` and ``dowel`` never add spare ledge cutouts.

``perch_clearance_mode=auto`` leaves a 10 mm gap between the bottom edge of
each opening and the nearest edge of its perch mount. For a dowel this is the
top edge of the circular hole; for a ledge it is the top edge of the
through-tab slot. Select ``manual`` and set ``perch_clearance`` to use an exact
gap in millimetres, for example ``perch_clearance=17``. The shared setting
applies independently below every enabled opening, so changing an opening's
height preserves the requested clearance. A clearance that would move a mount
outside its wall is rejected.

For ledges, select ``perch_size_mode=auto`` to derive proportions from the
opening and material thickness, or ``manual`` and provide positive
``perch_ledge_width`` and ``perch_ledge_depth`` values. Each ledge has a
centered through-tab that fits a matching slot below its opening, keeping the
ledge square during assembly. Glue the fitted joint for final strength.

``perch_ledge_tab_width_mode=auto`` makes the tab one third of the ledge
width (with material-aware minimum shoulders). Select ``manual`` and provide
``perch_ledge_tab_width`` to override it in millimetres. The tab depth remains
the material thickness so it fits the wall slot. ``perch_projection`` applies
only to a supplied dowel; ledge depth is ``perch_ledge_depth``.

All BirdHouse cutouts are packed from their exact rendered bounds using a
deterministic best-fit layout. Parts may rotate 90 degrees to reduce material
use. ``sheet_width`` sets the maximum physical cut-layout width in millimetres
(default 600 mm); the output height is minimized while preserving the
configured spacing and preventing cutout overlap.
