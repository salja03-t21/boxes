from __future__ import annotations

import math
from io import BytesIO

import pytest
from lxml import etree
from svgpathtools import parse_path

from boxes.generators.birdhouse import BirdHouse


SIDES = ("front", "back", "left", "right")


def render_birdhouse(*, enabled: tuple[str, ...], perch_mode: str = "ledge") -> bytes:
    args = [
        "--x=140", "--y=120", "--h=160", f"--perch_mode={perch_mode}",
        "--perch_size_mode=manual", "--perch_ledge_width=30",
        "--perch_ledge_depth=30", "--sheet_width=600", "--labels=1",
    ]
    for side in SIDES:
        shape = "circle" if side in enabled else "none"
        args.extend([f"--{side}_opening_shape={shape}", f"--{side}_opening_width=32"])

    box = BirdHouse()
    box.parseArgs(args)
    box.metadata["reproducible"] = True
    box.open()
    box.render()
    output: BytesIO = box.close()
    return output.getvalue()


def svg_text(svg: bytes) -> set[str]:
    root = etree.fromstring(svg)
    return {text for text in root.itertext() if text.strip()}


def physical_part_bboxes(svg: bytes) -> list[tuple[float, float, float, float]]:
    root = etree.fromstring(svg)
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    bboxes = []
    for group in root.xpath("./svg:g", namespaces=namespace):
        if any("burn:" in text for text in group.itertext()):
            continue
        path_bboxes = [
            parse_path(path.get("d", "")).bbox()
            for path in group.xpath(".//svg:path", namespaces=namespace)
            if path.get("d")
        ]
        if not path_bboxes:
            continue
        bboxes.append((
            min(box[0] for box in path_bboxes),
            min(box[2] for box in path_bboxes),
            max(box[1] for box in path_bboxes),
            max(box[3] for box in path_bboxes),
        ))
    return bboxes


def assert_part_spacing(
    bboxes: list[tuple[float, float, float, float]], minimum: float
) -> None:
    for index, first in enumerate(bboxes):
        for second in bboxes[index + 1:]:
            horizontal_gap = max(second[0] - first[2], first[0] - second[2], 0)
            vertical_gap = max(second[1] - first[3], first[1] - second[3], 0)
            assert horizontal_gap >= minimum or vertical_gap >= minimum, (
                f"part bounds overlap or violate spacing: {first}, {second}"
            )


def polygon_vertices(borders: list[float | None]) -> list[tuple[float, float]]:
    """Return vertices for Boxes.py's alternating length/turn representation."""
    x = y = angle = 0.0
    vertices = [(x, y)]
    for index in range(0, len(borders), 2):
        length = borders[index]
        if length is None:
            break
        x += length * math.cos(math.radians(angle))
        y += length * math.sin(math.radians(angle))
        vertices.append((x, y))
        if index + 1 >= len(borders) or borders[index + 1] is None:
            break
        angle += borders[index + 1]
    return vertices


def test_ledge_polygon_closes_without_an_extra_cut_line() -> None:
    box = BirdHouse()
    box.parseArgs([])

    borders = box.ledgeBorders(30, 30, 10)
    closed = box._closePolygon(borders.copy())
    vertices = polygon_vertices(borders)
    xs, ys = zip(*vertices)

    assert closed[-2] == pytest.approx(0, abs=1e-9)
    assert max(xs) - min(xs) == pytest.approx(30)
    assert max(ys) - min(ys) == pytest.approx(33)
    assert max(length for length in closed[::2] if length is not None) <= 30


@pytest.mark.parametrize(
    "enabled",
    [(), ("front",), ("front", "back"), SIDES],
)
def test_ledge_parts_exist_only_for_enabled_openings(enabled: tuple[str, ...]) -> None:
    svg = render_birdhouse(enabled=enabled)

    assert {text for text in svg_text(svg) if text.endswith(" perch")} == {
        f"{side} perch" for side in enabled
    }


def test_four_opening_layout_has_no_overlaps_and_respects_sheet_width() -> None:
    bboxes = physical_part_bboxes(render_birdhouse(enabled=SIDES))

    assert len(bboxes) == 11
    assert_part_spacing(bboxes, minimum=1.25)
    assert max(box[2] for box in bboxes) - min(box[0] for box in bboxes) <= 600
