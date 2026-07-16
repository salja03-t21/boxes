from pathlib import Path


ROOT = Path(__file__).parents[1]
DOCKERFILE = (ROOT / "scripts" / "Dockerfile").read_text()
COMPOSE_FILE = (ROOT / "docker-compose.yml").read_text()


def test_container_build_uses_checked_out_source() -> None:
    assert "ADD https://github.com/florianfesti/boxes.git" not in DOCKERFILE
    assert "COPY . /app" in DOCKERFILE


def test_container_runs_as_non_root() -> None:
    assert "USER boxes" in DOCKERFILE


def test_container_exposes_web_server() -> None:
    assert "EXPOSE 8000" in DOCKERFILE
    assert '"boxes.scripts.boxesserver"' in DOCKERFILE
    assert "boxes.scripts.boxesserver" in COMPOSE_FILE
