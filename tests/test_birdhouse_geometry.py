from __future__ import annotations

import math
from io import BytesIO

import pytest
from lxml import etree

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
