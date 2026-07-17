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
