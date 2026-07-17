from __future__ import annotations

from io import BytesIO

import pytest
from lxml import etree

from boxes.generators.birdhouse import BirdHouse
from boxes.generators.universalbox import UniversalBox


def render_svg(generator_type: type, args: list[str]) -> bytes:
    box = generator_type()
    box.parseArgs(args)
    box.metadata["reproducible"] = True
    box.open()
    box.render()
    output: BytesIO = box.close()
    svg = output.getvalue()
    etree.fromstring(svg)
    return svg


@pytest.mark.parametrize(
    ("position", "mode"),
    [("front", "blank"), ("back", "text")],
)
def test_universal_box_renders_partial_cover(position: str, mode: str) -> None:
    svg = render_svg(
        UniversalBox,
        [
            "--x=120",
            "--y=90",
            "--h=60",
            "--top_edge=e",
            f"--cover_position={position}",
            f"--cover_mode={mode}",
            "--cover_depth_mode=percent",
            "--cover_depth=33.3",
            "--cover_label=M3 screws",
        ],
    )

    assert len(svg) > 100
    if mode == "text":
        assert b"M3 screws" in svg


def test_universal_box_accepts_millimetre_cover_depth() -> None:
    svg = render_svg(
        UniversalBox,
        [
            "--x=120",
            "--y=90",
            "--h=60",
            "--top_edge=e",
            "--cover_mode=blank",
            "--cover_depth_mode=mm",
            "--cover_depth=30",
        ],
    )

    assert len(svg) > 100


def test_universal_box_rejects_cover_deeper_than_box() -> None:
    with pytest.raises(ValueError, match="cover depth"):
        render_svg(
            UniversalBox,
            [
                "--x=120",
                "--y=90",
                "--h=60",
                "--top_edge=e",
                "--cover_mode=blank",
                "--cover_depth_mode=mm",
                "--cover_depth=90",
            ],
        )


@pytest.mark.parametrize(
    ("side", "shape", "width", "height"),
    [
        ("front", "circle", 32, 32),
        ("back", "rectangle", 38, 28),
        ("left", "oval", 34, 24),
        ("right", "none", 0, 0),
    ],
)
def test_birdhouse_renders_independent_openings(
    side: str, shape: str, width: int, height: int
) -> None:
    svg = render_svg(
        BirdHouse,
        [
            "--x=140",
            "--y=120",
            "--h=160",
            f"--{side}_opening_shape={shape}",
            f"--{side}_opening_width={width}",
            f"--{side}_opening_height={height}",
            "--perch_mode=none",
        ],
    )

    assert len(svg) > 100


@pytest.mark.parametrize(
    ("perch_mode", "perch_size_mode"),
    [("dowel", "auto"), ("ledge", "auto"), ("ledge", "manual")],
)
def test_birdhouse_renders_shared_perches(
    perch_mode: str, perch_size_mode: str
) -> None:
    svg = render_svg(
        BirdHouse,
        [
            "--x=140",
            "--y=120",
            "--h=160",
            "--front_opening_shape=circle",
            "--front_opening_width=32",
            "--back_opening_shape=oval",
            "--back_opening_width=36",
            "--back_opening_height=24",
            f"--perch_mode={perch_mode}",
            f"--perch_size_mode={perch_size_mode}",
            "--perch_diameter=8",
            "--perch_projection=18",
            "--perch_ledge_width=42",
            "--perch_ledge_depth=22",
        ],
    )

    assert len(svg) > 100


def test_birdhouse_rejects_invalid_manual_ledge_size() -> None:
    with pytest.raises(ValueError, match="ledge"):
        render_svg(
            BirdHouse,
            [
                "--front_opening_shape=circle",
                "--front_opening_width=32",
                "--perch_mode=ledge",
                "--perch_size_mode=manual",
                "--perch_ledge_width=0",
                "--perch_ledge_depth=22",
            ],
        )


def test_birdhouse_ledge_tab_uses_a_centered_material_thickness_slot() -> None:
    box = BirdHouse()
    box.parseArgs(["--perch_mode=ledge"])
    slots: list[tuple[float, float, float, float]] = []
    box.rectangularHole = lambda x, y, dx, dy: slots.append((x, y, dx, dy))

    box.ledgeMount(70, 80, 32)

    assert slots == [(70, 62.5, box.thickness, box.thickness)]


def test_birdhouse_circle_opening_uses_width_as_its_only_dimension() -> None:
    box = BirdHouse()
    box.parseArgs([
        "--front_opening_shape=circle", "--front_opening_width=32",
        "--front_opening_height=80",
    ])

    assert box.openingDimensions("front", 140, 160) == ("circle", 32, 32)


def test_birdhouse_ledge_tab_width_defaults_to_one_third_of_ledge_width() -> None:
    box = BirdHouse()
    box.parseArgs(["--perch_mode=ledge", "--perch_ledge_tab_width_mode=auto"])

    assert box.ledgeTabWidth(30) == 10


def test_birdhouse_ledge_tab_width_accepts_manual_value() -> None:
    box = BirdHouse()
    box.parseArgs([
        "--perch_mode=ledge", "--perch_ledge_tab_width_mode=manual",
        "--perch_ledge_tab_width=18",
    ])

    assert box.ledgeTabWidth(30) == 18


def test_universal_box_partial_cover_uses_finger_joint_side_edges() -> None:
    box = UniversalBox()
    box.parseArgs([
        "--x=120", "--y=90", "--h=60", "--top_edge=e",
        "--cover_mode=blank", "--cover_depth_mode=mm", "--cover_depth=30",
    ])
    parts: list[tuple[float, float, str, str]] = []
    box.rectangularWall = lambda x, y, edges, **kwargs: parts.append(
        (x, y, edges, kwargs["label"])
    )

    box.partialCover(120, 90)

    assert parts == [(120, 30, "effe", "partial top cover (back)")]


def test_universal_box_partial_cover_slot_matches_selected_end() -> None:
    box = UniversalBox()
    box.parseArgs([
        "--y=90", "--h=60", "--top_edge=e", "--cover_mode=blank",
        "--cover_position=back", "--cover_depth_mode=mm", "--cover_depth=30",
    ])
    slots: list[tuple[float, float, float, int]] = []
    box.fingerHolesAt = lambda x, y, length, angle: slots.append((x, y, length, angle))

    box.partialCoverSlot(90, 60)

    assert slots == [(60, 58.5, 30, 0)]
