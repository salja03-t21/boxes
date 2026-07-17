from __future__ import annotations

import math
from collections import Counter
from io import BytesIO
from urllib.parse import urlencode

import pytest
from lxml import etree
from svgpathtools import parse_path

from boxes.generators.birdhouse import BirdHouse
from boxes.scripts.boxesserver import BServer


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


def rendered_opening_sizes(svg: bytes) -> Counter[tuple[float, float]]:
    """Return normalized bounds for blue cutouts large enough to be openings."""
    root = etree.fromstring(svg)
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    sizes = Counter()
    for element in root.xpath(
        './/svg:path[@stroke="rgb(0,0,255)"]', namespaces=namespace
    ):
        xmin, xmax, ymin, ymax = parse_path(element.get("d", "")).bbox()
        dimensions = sorted((xmax - xmin, ymax - ymin))
        if dimensions[0] > 15:
            sizes[(round(dimensions[0], 1), round(dimensions[1], 1))] += 1
    return sizes


def assert_all_cut_paths_closed(svg: bytes) -> None:
    root = etree.fromstring(svg)
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    for element in root.xpath(".//svg:path[@d]", namespaces=namespace):
        path = parse_path(element.get("d", ""))
        assert path.isclosed(), f"open cut path: {element.get('d', '')}"


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


def backend_render_birdhouse(parameters: dict[str, str | float]) -> bytes:
    response: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        response["status"] = status
        response["headers"] = headers

    def file_wrapper(file: BytesIO, block_size: int):
        while chunk := file.read(block_size):
            yield chunk

    query = {"render": "1", "format": "svg", "labels": "1", **parameters}
    environ = {
        "PATH_INFO": "/BirdHouse",
        "QUERY_STRING": urlencode(query),
        "REQUEST_METHOD": "GET",
        "wsgi.url_scheme": "http",
        "wsgi.file_wrapper": file_wrapper,
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8000",
        "HTTP_HOST": "localhost:8000",
        "HTTP_ACCEPT_LANGUAGE": "en",
    }
    body = b"".join(BServer().serve(environ, start_response))

    assert response["status"] == "200 OK"
    headers = dict(response["headers"])
    assert headers["Content-type"].startswith("image/svg+xml")
    etree.fromstring(body)
    return body


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
    ("mode", "configured", "expected"),
    [("auto", 3, 10), ("manual", 17, 17)],
)
def test_perch_clearance(mode: str, configured: float, expected: float) -> None:
    box = BirdHouse()
    box.parseArgs([
        f"--perch_clearance_mode={mode}",
        f"--perch_clearance={configured}",
    ])

    assert box.perchClearance() == expected


def test_perch_mount_position_uses_edge_to_edge_clearance() -> None:
    box = BirdHouse()
    box.parseArgs([
        "--perch_clearance_mode=manual",
        "--perch_clearance=17",
    ])

    assert box.perchMountY(80, 40, 8) == 39


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (
            ["--perch_clearance_mode=manual", "--perch_clearance=-1"],
            "perch clearance must not be negative",
        ),
        (
            ["--perch_clearance_mode=manual", "--perch_clearance=60"],
            "perch clearance places the mount outside the wall",
        ),
    ],
)
def test_invalid_perch_clearance_is_rejected(
    args: list[str], message: str
) -> None:
    box = BirdHouse()
    box.parseArgs(args)

    with pytest.raises(ValueError, match=message):
        box.perchMountY(80, 40, 8)


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
    assert max(box[3] for box in bboxes) - min(box[1] for box in bboxes) <= 470


@pytest.mark.parametrize(
    ("perch_mode", "size_mode", "tab_mode", "dimensions", "sheet_width"),
    [
        ("none", "auto", "auto", (120, 100, 140), 300),
        ("dowel", "auto", "auto", (160, 110, 180), 400),
        ("ledge", "auto", "auto", (140, 120, 160), 600),
        ("ledge", "manual", "manual", (180, 130, 200), 300),
    ],
)
@pytest.mark.parametrize("enabled_mask", range(16))
def test_backend_svg_option_matrix_is_clean(
    perch_mode: str,
    size_mode: str,
    tab_mode: str,
    dimensions: tuple[int, int, int],
    sheet_width: int,
    enabled_mask: int,
) -> None:
    enabled = tuple(
        side for index, side in enumerate(SIDES) if enabled_mask & (1 << index)
    )
    shapes = {"front": "circle", "back": "rectangle", "left": "oval", "right": "circle"}
    opening_sizes = {
        "front": (31, 31),
        "back": (34, 22),
        "left": (37, 25),
        "right": (29, 29),
    }
    x, y, h = dimensions
    parameters: dict[str, str | float] = {
        "x": x,
        "y": y,
        "h": h,
        "perch_mode": perch_mode,
        "perch_size_mode": size_mode,
        "perch_ledge_width": 30,
        "perch_ledge_depth": 30,
        "perch_ledge_tab_width_mode": tab_mode,
        "perch_ledge_tab_width": 10,
        "sheet_width": sheet_width,
    }
    for side in SIDES:
        parameters[f"{side}_opening_shape"] = shapes[side] if side in enabled else "none"
        width, height = opening_sizes[side]
        parameters[f"{side}_opening_width"] = width
        parameters[f"{side}_opening_height"] = height

    svg = backend_render_birdhouse(parameters)
    bboxes = physical_part_bboxes(svg)

    expected_parts = 7 + (len(enabled) if perch_mode == "ledge" else 0)
    assert len(bboxes) == expected_parts
    assert_all_cut_paths_closed(svg)
    assert_part_spacing(bboxes, minimum=1.25)
    assert max(box[2] for box in bboxes) - min(box[0] for box in bboxes) <= sheet_width
    expected_openings = Counter(
        tuple(sorted((width - 0.2, height - 0.2)))
        for side in enabled
        for width, height in [opening_sizes[side]]
    )
    assert rendered_opening_sizes(svg) == expected_openings
    assert {text for text in svg_text(svg) if text.endswith(" perch")} == (
        {f"{side} perch" for side in enabled} if perch_mode == "ledge" else set()
    )
