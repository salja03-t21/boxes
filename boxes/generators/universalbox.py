# Copyright (C) 2013-2014 Florian Festi
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from boxes import *
from boxes import lids
from boxes.edges import Bolts
from boxes.lids import _TopEdge


class UniversalBox(_TopEdge):
    """Box with various options for different styles and lids"""

    ui_group = "Box"

    def __init__(self) -> None:
        Boxes.__init__(self)
        self.addTopEdgeSettings(roundedtriangle={"outset" : 1},
                                hinge={"outset" : True})
        self.addSettingsArgs(edges.FlexSettings)
        self.addSettingsArgs(lids.LidSettings)
        self.buildArgParser("top_edge", "bottom_edge",
                            "x", "y", "h", "outside")
        self.argparser.add_argument(
            "--vertical_edges",  action="store", type=str,
            default="finger joints",
            choices=("finger joints", "finger holes"),
            help="connections used for the vertical edges")
        self.argparser.add_argument(
            "--cover_mode", action="store", type=str, default="none",
            choices=("none", "blank", "text"),
            help="fixed partial top cover")
        self.argparser.add_argument(
            "--cover_position", action="store", type=str, default="back",
            choices=("front", "back"),
            help="end of the box covered by the partial top")
        self.argparser.add_argument(
            "--cover_depth_mode", action="store", type=str, default="percent",
            choices=("percent", "mm"),
            help="interpret cover depth as a percentage of box depth or millimetres")
        self.argparser.add_argument(
            "--cover_depth", action="store", type=float, default=33.3,
            help="partial-cover depth, as selected by cover_depth_mode")
        self.argparser.add_argument(
            "--cover_label", action="store", type=str, default="",
            help="text engraved on a text partial top cover")

    def coverDepth(self, y):
        if self.cover_depth_mode == "percent":
            depth = y * self.cover_depth / 100.0
        else:
            depth = self.cover_depth

        if depth <= 0 or depth >= y:
            raise ValueError("cover depth must be greater than zero and smaller than box depth")
        return depth

    def coverLabel(self, width, depth):
        if self.cover_mode == "text" and self.cover_label:
            fontsize = min(10, depth / 3, width / max(1, len(self.cover_label)))
            self.text(self.cover_label, width / 2, depth / 2,
                      align="center middle", fontsize=fontsize)

    def partialCover(self, x, y):
        if self.cover_mode == "none":
            return
        if self.top_edge != "e":
            raise ValueError("partial top cover requires top_edge=e")

        depth = self.coverDepth(y)
        t = self.thickness
        width = x + 2 * t
        label = "partial top cover (%s)" % self.cover_position

        self.rectangularWall(width, depth, "eeee",
                             callback=[lambda: self.coverLabel(width, depth)],
                             move="up", label=label)
        # Two rails glue beneath the cover and against the side walls. They
        # locate the strip at the selected end and make the fixed cover easy
        # to assemble without changing the standard wall joints.
        self.rectangularWall(depth, t, "eeee", move="up",
                             label="partial cover support left")
        self.rectangularWall(depth, t, "eeee", move="up",
                             label="partial cover support right")

    def top_hole(self, x, y, top_edge):
        t = self.thickness

        if top_edge == "f":
            edge = self.edges["F"]
            self.moveTo(2*t+self.burn, 2*t, 90)
        elif top_edge == "F":
            edge = self.edges["f"]
            self.moveTo(t+self.burn, 2*t, 90)
        else:
            raise ValueError("Only f and F supported")

        for l in (y, x, y, x):
            edge(l)
            if top_edge == "F": self.edge(t)
            self.corner(-90)
            if top_edge == "F": self.edge(t)

    def render(self):
        x, y, h = self.x, self.y, self.h
        t = self.thickness

        tl, tb, tr, tf = self.topEdges(self.top_edge)
        b = self.edges.get(self.bottom_edge, self.edges["F"])

        d2 = Bolts(2)
        d3 = Bolts(3)

        d2 = d3 = None

        sideedge = "F" if self.vertical_edges == "finger joints" else "h"

        if self.outside:
            self.x = x = self.adjustSize(x, sideedge, sideedge)
            self.y = y = self.adjustSize(y)
            self.h = h = self.adjustSize(h, b, self.top_edge)

        ignore_widths = [1, 6]
        if self.top_edge in "ik":
            self.edges[self.top_edge].settings.style = "flush_inset"
            ignore_widths = [1, 3, 4, 6]

        with self.saved_context():
            self.rectangularWall(x, h, [b, sideedge, tf, sideedge],
                                 ignore_widths=ignore_widths,
                                 bedBolts=[d2], move="up", label="front")
            self.rectangularWall(x, h, [b, sideedge, tb, sideedge],
                                 ignore_widths=ignore_widths,
                                 bedBolts=[d2], move="up", label="back")

            if self.bottom_edge != "e":
                self.rectangularWall(x, y, "ffff", bedBolts=[d2, d3, d2, d3], move="up", label="bottom")
            if self.top_edge in "fF":
                self.set_source_color(Color.MAGENTA)    # I don't know why this part has a different color, but RED is not a good choice because RED is used for annotations
                self.rectangularWall(x+4*t, y+4*t, callback=[
                    lambda:self.top_hole(x, y, self.top_edge)], move="up", label="top hole")
                self.set_source_color(Color.BLACK)

            self.drawLid(x, y, self.top_edge, [d2, d3])
            self.lid(x, y, self.top_edge)
            self.partialCover(x, y)

        self.rectangularWall(x, h, [b, sideedge, tf, sideedge],
                             ignore_widths=ignore_widths,
                             bedBolts=[d2], move="right only", label="invisible")
        self.rectangularWall(y, h, [b, "f", tl, "f"],
                             ignore_widths=ignore_widths,
                             bedBolts=[d3], move="up", label="left")
        self.rectangularWall(y, h, [b, "f", tr, "f"],
                             ignore_widths=ignore_widths,
                             bedBolts=[d3], move="up", label="right")
