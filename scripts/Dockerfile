FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN python -m venv /app/env \
    && /app/env/bin/pip install --upgrade pip gunicorn

COPY . /app
RUN /app/env/bin/pip install .

FROM python:3.12-slim AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends pstoedit \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 boxes

WORKDIR /app
COPY --from=builder /app /app

ENV PATH=/app/env/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    STATIC_URL=/static

USER boxes
EXPOSE 8000

CMD ["/app/env/bin/gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--access-logfile", "-", "--error-logfile", "-", "boxes.scripts.boxesserver"]
