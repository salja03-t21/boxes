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

The SVG includes the cover and two support rails. Glue the rails beneath the
cover, against the inside faces of the two side walls, then glue the assembly
at the selected end of the box.

BirdHouse openings and perches
------------------------------

BirdHouse exposes opening controls for ``front``, ``back``, ``left``, and
``right`` independently. For each side select ``<side>_opening_shape`` as
``none``, ``circle``, ``rectangle``, or ``oval``. Use the matching width and
height fields to set the size; circles use width as their diameter. A zero
dimension preserves the original automatic proportion for a rectangular
opening. Openings remain centred on their wall.

``perch_mode`` applies the same choice below every enabled opening:

* ``none`` adds no perch;
* ``dowel`` cuts a mounting hole using ``perch_diameter``. Supply a dowel and
  install it with the desired ``perch_projection``;
* ``ledge`` adds one laser-cut ledge panel for each enabled opening.

For ledges, select ``perch_size_mode=auto`` to derive proportions from the
opening and material thickness, or ``manual`` and provide positive
``perch_ledge_width`` and ``perch_ledge_depth`` values. Glue each generated
ledge directly below its matching opening.
