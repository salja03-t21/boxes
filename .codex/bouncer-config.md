# Bouncer Configuration
# Refreshed from `~/.codex/bin/bouncer-init` on 2026-07-17 - customized for Boxes.py.

## Backend
lint_command: "SKIP=autoflake,rstcheck,pytest .venv/bin/pre-commit run --all-files"
test_command: ".venv/bin/pytest -q -n auto"
coverage_command: ".venv/bin/coverage erase && .venv/bin/coverage run -m pytest -q tests/test_configurable_generators.py tests/test_birdhouse_geometry.py && .venv/bin/coverage report --fail-under=75 -m boxes/generators/birdhouse.py"
coverage_threshold: 75

## Frontend
frontend_lint: ""
frontend_test: ""

## Conventions
commit_convention: "conventional"

## Extra Security Rules
extra_security_rules:
  - "All SQL queries MUST use parameterized placeholders -- never string interpolation"
  - "Never use eval() or exec() on user input"

## Excluded Paths
excluded_paths:
  - "node_modules"
  - ".venv"
  - "__pycache__"
  - "dist"
  - "build"
  - ".dart_tool"

## Notes
notes:
  - "BirdHouse application changes use both configurable-generator and backend SVG geometry tests for focused coverage."
  - "On macOS, autoflake and rstcheck must be run one process/file at a time if the host POSIX semaphore pool is exhausted."
  - "The pytest pre-commit hook uses the system interpreter; Bouncer deliberately uses the project virtualenv."
  - "Install the declared dev extras before running Bouncer so coverage and pytest-xdist are available."
