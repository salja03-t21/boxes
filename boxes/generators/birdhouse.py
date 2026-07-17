# Copyright (C) 2013-2022 Florian Festi
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

from dataclasses import dataclass
import math
from typing import Callable

import rectpack
from rectpack import newPacker, PackingBin

from boxes import *


@dataclass(frozen=True)
class BirdHousePart:
    name: str
    width: float
    height: float
    render: Callable[[str | None], None]


class BirdHouse(Boxes):
    """Simple Bird House"""

    ui_group = "Misc"

    def __init__(self) -> None:
        Boxes.__init__(self)

        self.addSettingsArgs(edges.FingerJointSettings, finger=10.0,space=10.0)
        self.buildArgParser(x=200, y=200, h=200)
        self.argparser.add_argument(
            "--roof_overhang",  action="store", type=float, default=0.4,
            help="overhang as fraction of the roof length")
        for side in ("front", "back", "left", "right"):
            self.argparser.add_argument(
                f"--{side}_opening_shape", action="store", type=str,
                choices=("none", "circle", "rectangle", "oval"),
                default="rectangle",
                help=f"opening shape on the {side} wall")
            self.argparser.add_argument(
                f"--{side}_opening_width", action="store", type=float,
                default=0.0, help=f"opening width or diameter on the {side} wall")
            self.argparser.add_argument(
                f"--{side}_opening_height", action="store", type=float,
                default=0.0,
                help=f"opening height on the {side} wall (ignored for circles)")
        self.argparser.add_argument(
            "--perch_mode", action="store", type=str, default="none",
            choices=("none", "dowel", "ledge"),
            help="shared perch added below each opening")
        self.argparser.add_argument(
            "--perch_size_mode", action="store", type=str, default="auto",
            choices=("auto", "manual"),
            help="derive ledge dimensions automatically or use manual values")
        self.argparser.add_argument(
            "--perch_diameter", action="store", type=float, default=8.0,
            help="dowel diameter")
        self.argparser.add_argument(
            "--perch_projection", action="store", type=float, default=18.0,
            help="distance a supplied dowel projects from the wall")
        self.argparser.add_argument(
            "--perch_ledge_width", action="store", type=float, default=0.0,
            help="manual integrated ledge width")
        self.argparser.add_argument(
            "--perch_ledge_depth", action="store", type=float, default=0.0,
            help="manual integrated ledge depth")
        self.argparser.add_argument(
            "--perch_ledge_tab_width_mode", action="store", type=str,
            choices=("auto", "manual"), default="auto",
            help="derive ledge tab width automatically or use a manual value")
        self.argparser.add_argument(
            "--perch_ledge_tab_width", action="store", type=float, default=0.0,
            help="manual ledge through-tab width")
        self.argparser.add_argument(
            "--sheet_width", action="store", type=float, default=600.0,
            help="maximum width used to pack BirdHouse cutouts")

    def sideSize(self, x, h, edges="hfeffef"):
        edges = [self.edges.get(e, e) for e in edges]
        edges.append(edges[0])  # wrap around
        tw = x + edges[1].spacing() + edges[-2].spacing()
        th = (h + x / 2 + self.thickness + edges[0].spacing()
              + max(edges[3].spacing(), edges[4].spacing()))
        return tw, th

    def side(self, x, h, edges="hfeffef", callback=None, move=None):
        angles = (90, 0, 45, 90, 45, 0, 90)
        roof = 2**0.5 * x / 2
        t = self.thickness
        lengths = (x, h, t, roof, roof, t, h)

        tw, th = self.sideSize(x, h, edges)
        edges = [self.edges.get(e, e) for e in edges]
        edges.append(edges[0])  # wrap around

        if self.move(tw, th, move, True):
            return

        self.moveTo(edges[-2].spacing())
        for i in range(7):
            self.cc(callback, i, y=self.burn+edges[i].startWidth())
            edges[i](lengths[i])
            self.edgeCorner(edges[i], edges[i+1], angles[i])

        self.move(tw, th, move)

    def roofSize(self, x, h, overhang, edges="eefe"):
        edges = [self.edges.get(e, e) for e in edges]
        tw = (x + 2 * self.thickness + 2 * overhang
              + edges[1].spacing() + edges[3].spacing())
        th = (h + 2 * self.thickness + overhang
              + edges[0].spacing() + edges[2].spacing())
        return tw, th

    def roof(self, x, h, overhang, edges="eefe", move=None):
        t = self.thickness
        edges = [self.edges.get(e, e) for e in edges]

        tw, th = self.roofSize(x, h, overhang, edges)

        if self.move(tw, th, move, True):
            return

        self.moveTo(overhang + edges[3].spacing(), edges[0].margin())
        edges[0](x + 2*t)
        self.corner(90, overhang)
        edges[1](h + 2*t)
        self.edgeCorner(edges[1], edges[2])
        self.fingerHolesAt(overhang + 0.5*t, edges[2].startWidth(), h, 90)
        self.fingerHolesAt(x + overhang + 1.5*t, edges[2].startWidth(), h, 90)
        edges[2](x + 2*t + 2*overhang)
        self.edgeCorner(edges[2], edges[3])
        edges[3](h + 2*t)
        self.corner(90, overhang)

        self.move(tw, th, move)

    def openingDimensions(self, side, width, height):
        shape = getattr(self, f"{side}_opening_shape")
        if shape == "none":
            return None

        opening_width = getattr(self, f"{side}_opening_width") or 0.75 * width
        opening_height = getattr(self, f"{side}_opening_height") or 0.75 * height
        if shape == "circle":
            opening_height = opening_width

        if opening_width <= 0 or opening_height <= 0:
            raise ValueError("opening dimensions must be greater than zero")
        if opening_width >= width or opening_height >= height:
            raise ValueError("opening dimensions must fit inside the wall")
        return shape, opening_width, opening_height

    def openingCallback(self, side, width, height):
        dimensions = self.openingDimensions(side, width, height)
        if dimensions is None:
            return None

        shape, opening_width, opening_height = dimensions

        def callback():
            x = width / 2
            y = height / 2
            if shape == "circle":
                self.hole(x, y, d=opening_width)
            elif shape == "rectangle":
                self.rectangularHole(x, y, opening_width, opening_height,
                                     r=self.thickness)
            else:
                self.rectangularHole(x, y, opening_width, opening_height,
                                     r=min(opening_width, opening_height) / 2)
            self.perchMount(x, y, opening_height)
            self.ledgeMount(x, y, opening_width, opening_height)

        return callback

    def perchMount(self, x, opening_y, opening_height):
        if self.perch_mode != "dowel":
            return
        if self.perch_diameter <= 0 or self.perch_projection <= 0:
            raise ValueError("dowel diameter and projection must be greater than zero")
        perch_y = max(self.thickness + self.perch_diameter / 2,
                      opening_y - opening_height / 2 - self.thickness - self.perch_diameter / 2)
        self.hole(x, perch_y, d=self.perch_diameter)

    def ledgeMount(self, x, opening_y, opening_width, opening_height):
        if self.perch_mode != "ledge":
            return
        t = self.thickness
        ledge_y = max(t / 2, opening_y - opening_height / 2 - t / 2)
        ledge_width, _ = self.ledgeDimensions(opening_width, opening_height)
        self.rectangularHole(x, ledge_y, self.ledgeTabWidth(ledge_width), t)

    def ledgeDimensions(self, opening_width, opening_height):
        if self.perch_size_mode == "auto":
            return max(2 * self.thickness, opening_width * 1.25), max(2 * self.thickness, opening_height / 2)
        if self.perch_ledge_width <= 0 or self.perch_ledge_depth <= 0:
            raise ValueError("manual ledge dimensions must be greater than zero")
        return self.perch_ledge_width, self.perch_ledge_depth

    def ledgeTabWidth(self, ledge_width):
        if self.perch_ledge_tab_width_mode == "manual":
            tab_width = self.perch_ledge_tab_width
        else:
            tab_width = max(2 * self.thickness, ledge_width / 3)
        if tab_width <= 0 or tab_width >= ledge_width:
            raise ValueError("ledge tab width must be greater than zero and smaller than ledge width")
        return tab_width

    def ledgeBorders(self, width, depth, tab):
        shoulder = (width - tab) / 2
        return [
            width, 90, depth, 90, shoulder, -90,
            self.thickness, 90, tab, 90, self.thickness, -90,
            shoulder, 90, depth, None,
        ]

    def rectangularWallSize(self, x, y, edges="eeee"):
        edges = [self.edges.get(edge, edge) for edge in edges]
        return (
            x + edges[3].spacing() + edges[1].spacing(),
            y + edges[0].spacing() + edges[2].spacing(),
        )

    def ledgeSize(self, width, depth, tab):
        borders = self._closePolygon(self.ledgeBorders(width, depth, tab))
        minx, miny, maxx, maxy = self._polygonWallExtend(
            borders, [self.edges["e"]]
        )
        return maxx - minx, maxy - miny

    def renderLedges(self, openings):
        if self.perch_mode != "ledge":
            return
        for side, opening_width, opening_height in openings:
            width, depth = self.ledgeDimensions(opening_width, opening_height)
            tab = self.ledgeTabWidth(width)
            self.polygonWall(
                self.ledgeBorders(width, depth, tab),
                edge="e", move="up", label=f"{side} perch")

    def packParts(self, parts: list[BirdHousePart]):
        if self.sheet_width <= 0:
            raise ValueError("sheet width must be greater than zero")

        padded_sizes = {}
        for index, part in enumerate(parts):
            padded = part.width + self.spacing, part.height + self.spacing
            if min(padded) > self.sheet_width:
                raise ValueError("sheet width is too small for a BirdHouse cutout")
            padded_sizes[index] = padded

        def pack_at_height(height):
            packer = newPacker(
                rotation=True,
                pack_algo=rectpack.MaxRectsBssf,
                bin_algo=PackingBin.Global,
                sort_algo=rectpack.SORT_AREA,
            )
            for index, padded in padded_sizes.items():
                packer.add_rect(*padded, rid=index)
            packer.add_bin(self.sheet_width, height)
            packer.pack()
            return packer.rect_list()

        total_area = sum(width * height for width, height in padded_sizes.values())
        lower_height = max(
            total_area / self.sheet_width,
            max(min(width, height) for width, height in padded_sizes.values()),
        )
        upper_height = sum(max(width, height) for width, height in padded_sizes.values())
        placements = pack_at_height(upper_height)
        if len(placements) != len(parts):
            raise ValueError("sheet width is too small for a BirdHouse cutout")

        while upper_height - lower_height > 0.5:
            candidate_height = (lower_height + upper_height) / 2
            candidate = pack_at_height(candidate_height)
            if len(candidate) == len(parts):
                upper_height = candidate_height
                placements = candidate
            else:
                lower_height = candidate_height

        placements = sorted(placements, key=lambda placement: placement[5])

        for _, x, y, packed_width, packed_height, index in placements:
            part = parts[index]
            original_width, original_height = padded_sizes[index]
            rotated = (
                math.isclose(packed_width, original_height)
                and math.isclose(packed_height, original_width)
                and not math.isclose(original_width, original_height)
            )
            with self.saved_context():
                self.moveTo(x, y)
                part.render("rotated" if rotated else None)

    def render(self):
        x, y, h = self.x, self.y, self.h

        roof = 2**0.5 * x / 2
        overhang = roof * self.roof_overhang

        front = self.openingCallback("front", x, h)
        back = self.openingCallback("back", x, h)
        left = self.openingCallback("left", y, h)
        right = self.openingCallback("right", y, h)

        self.edges["h"].settings.setValues(self.thickness, relative=False, edge_width=overhang)

        openings = []
        for side, width in (("front", x), ("back", x), ("left", y), ("right", y)):
            dimensions = self.openingDimensions(side, width, h)
            if dimensions is not None:
                _, opening_width, opening_height = dimensions
                openings.append((side, opening_width, opening_height))
        gable_size = self.sideSize(x, h)
        wall_size = self.rectangularWallSize(y, h, "hFeF")
        bottom_size = self.rectangularWallSize(x, y, "ffff")
        roof_size = self.roofSize(y, roof, overhang, "eefe")
        parts = [
            BirdHousePart("front", *gable_size,
                          lambda move: self.side(x, h, callback=[front], move=move)),
            BirdHousePart("back", *gable_size,
                          lambda move: self.side(x, h, callback=[back], move=move)),
            BirdHousePart("left", *wall_size,
                          lambda move: self.rectangularWall(
                              y, h, "hFeF", callback=[left], move=move)),
            BirdHousePart("right", *wall_size,
                          lambda move: self.rectangularWall(
                              y, h, "hFeF", callback=[right], move=move)),
            BirdHousePart("bottom", *bottom_size,
                          lambda move: self.rectangularWall(x, y, "ffff", move=move)),
            BirdHousePart("roof left", *roof_size,
                          lambda move: self.roof(y, roof, overhang, "eefe", move=move)),
            BirdHousePart("roof right", *roof_size,
                          lambda move: self.roof(y, roof, overhang, "eeFe", move=move)),
        ]
        if self.perch_mode == "ledge":
            for side, opening_width, opening_height in openings:
                width, depth = self.ledgeDimensions(opening_width, opening_height)
                tab = self.ledgeTabWidth(width)
                parts.append(BirdHousePart(
                    f"{side} perch", *self.ledgeSize(width, depth, tab),
                    lambda move, side=side, width=width, depth=depth, tab=tab:
                    self.polygonWall(
                        self.ledgeBorders(width, depth, tab),
                        edge="e", move=move, label=f"{side} perch")))
        self.packParts(parts)
