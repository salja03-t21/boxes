# Boxes.py Homelab Swarm Deployment Implementation Plan

> **For Codex:** REQUIRED SKILLS: Use `executing-plans` for execution and
> `codex-serena-beads-workflow` for Serena + Beads workflow discipline. Before
> implementation also use `test-driven-development`; before handoff use
> `verification-before-completion`, `bouncer-init` where needed, and `bouncer`.

**Goal:** Publish an enhancement-ready Boxes.py image from
`salja03-t21/boxes` and run it at `http://boxes.ciothoughts.net` on the
LAN-only Docker Swarm at `10.0.5.12`.

**Architecture:** The existing Open Brain Traefik service remains the only
proxy. It retains port 3000, additionally publishes LAN port 80, and joins a
shared external `lan-ingress` overlay. A stateless `boxes` stack joins that
overlay without publishing a port and is selected by a host-specific Traefik
router. OPNsense Unbound resolves the private hostname; no public DNS,
Cloudflare route, or WAN forwarding is created.

**Tech Stack:** Python 3.12, Gunicorn/WSGI, Docker Buildx, GHCR, Docker Swarm,
Traefik v2.11, OPNsense Unbound, GitHub Actions.

---

## Execution prerequisites and tracking

- Boxes worktree:
  `/Users/jamessalmon/.config/superpowers/worktrees/boxes/homelab-swarm-deployment`
- Boxes branch: `feat/homelab-swarm-deployment`, based on `fork/master`
- Homelab local history must remain untouched at
  `/Users/jamessalmon/Repositories/homelab`.
- Open Brain feature work must start from `origin/dev` and promote
  `feature -> dev -> main` through PRs.
- Serena is configured globally for an unrelated Omi repository and is not
  discoverable in the current session. At execution start, attempt activation
  for each active worktree. If it remains unavailable, record that fact in the
  Beads parent issue and use targeted `rg`/`apply_patch` fallback.
- Context7 was checked during planning. Traefik v2 Swarm labels belong under
  `deploy.labels`; `traefik.docker.network` must select the shared overlay when
  multiple networks are present.
- Neither Boxes nor homelab currently uses Beads. Initialize stealth tracking
  in the Boxes worktree so tracking does not enter the upstream-derived repo:

```bash
bd init --stealth --prefix boxes
PARENT=$(bd create "Deploy Boxes.py to homelab Swarm" --type epic --priority P1 --silent)
bd create "Make fork image reproducible" --type task --parent "$PARENT"
bd create "Share Open Brain Traefik LAN ingress" --type task --parent "$PARENT"
bd create "Add homelab stack and runbook" --type task --parent "$PARENT"
bd create "Add OPNsense internal DNS" --type task --parent "$PARENT"
bd create "Deploy and verify LAN-only service" --type task --parent "$PARENT"
```

Mirror the active child in `update_plan`; only one item may be in progress.

### Task 1: Make the fork container build from checked-out source

**Files:**

- Create: `.dockerignore`
- Create: `tests/test_container_contract.py`
- Modify: `scripts/Dockerfile`

**Step 1: Write the failing container-contract tests**

Create `tests/test_container_contract.py`:

```python
from pathlib import Path


ROOT = Path(__file__).parents[1]
DOCKERFILE = (ROOT / "scripts" / "Dockerfile").read_text()


def test_container_build_uses_checked_out_source() -> None:
    assert "ADD https://github.com/florianfesti/boxes.git" not in DOCKERFILE
    assert "COPY . /app" in DOCKERFILE


def test_container_runs_as_non_root() -> None:
    assert "USER boxes" in DOCKERFILE


def test_container_exposes_web_server() -> None:
    assert "EXPOSE 8000" in DOCKERFILE
    assert '"scripts.boxesserver"' in DOCKERFILE
```

**Step 2: Run the tests and confirm the intended failure**

Run:

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_container_contract.py -q
```

Expected: FAIL because the existing Dockerfile uses remote `ADD` and has no
non-root user or exposed-port declaration.

**Step 3: Replace the Dockerfile with a local-source multi-stage build**

Use this shape in `scripts/Dockerfile`:

```dockerfile
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

CMD ["/app/env/bin/gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--access-logfile", "-", "--error-logfile", "-", "scripts.boxesserver"]
```

Create `.dockerignore` containing at least:

```text
.git
.github
.venv
env
venv
build
dist
*.egg-info
*.pyc
__pycache__
.pytest_cache
.mypy_cache
docs/plans
```

Do not exclude `static`, `po`, `boxes`, or `scripts`; the installed web app
needs them.

**Step 4: Run the focused and full Python suites**

Run:

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_container_contract.py -q
PYTHONPATH=. .venv/bin/pytest -q
```

Expected: focused test PASS; full suite approximately `193 passed, 9 skipped`
plus the three new passing contract tests.

**Step 5: Build and smoke-test the amd64 image**

Run:

```bash
docker buildx build --platform linux/amd64 --load \
  -f scripts/Dockerfile -t boxes:homelab-test .
docker run --rm -d --name boxes-homelab-test -p 127.0.0.1:4455:8000 \
  boxes:homelab-test
curl --fail --retry 20 --retry-delay 1 http://127.0.0.1:4455/ >/tmp/boxes-index.html
curl --fail --get 'http://127.0.0.1:4455/ABox' \
  --data-urlencode 'x=100' --data-urlencode 'y=100' \
  --data-urlencode 'h=100' --data-urlencode 'render=1' \
  -o /tmp/boxes-smoke.svg
rg '<svg' /tmp/boxes-smoke.svg
docker rm -f boxes-homelab-test
```

Expected: both HTTP calls succeed, the generated file contains `<svg`, and
the container is removed.

**Step 6: Commit**

```bash
git add .dockerignore scripts/Dockerfile tests/test_container_contract.py
git commit -m "build: package local source in container image"
```

### Task 2: Make fork CI publish an immutable amd64 image

**Files:**

- Modify: `.github/workflows/docker-publish.yml`
- Create: `docs/deployment/homelab.md`
- Modify: `README.rst`

**Step 1: Write a failing workflow-contract test**

Extend `tests/test_container_contract.py`:

```python
WORKFLOW = (ROOT / ".github" / "workflows" / "docker-publish.yml").read_text()


def test_container_workflow_publishes_immutable_amd64_sha_tag() -> None:
    assert "platforms: linux/amd64" in WORKFLOW
    assert "type=sha,prefix=sha-" in WORKFLOW
```

Run the focused test and confirm it fails.

**Step 2: Update the workflow**

Keep the upstream signed-image workflow, but make these outcomes explicit:

```yaml
permissions:
  contents: read
  packages: write
  id-token: write

# metadata-action tags input
tags: |
  type=sha,prefix=sha-
  type=ref,event=tag

# build-push-action inputs
platforms: linux/amd64
push: ${{ github.event_name != 'pull_request' }}
```

Remove the daily scheduled publish. Publish only for reviewed changes merged
to `master`, manual dispatch, and release tags. PRs build without pushing.

**Step 3: Document ownership and release flow**

Create `docs/deployment/homelab.md` covering:

- fork: `https://github.com/salja03-t21/boxes`;
- upstream: `https://github.com/florianfesti/boxes`;
- local repo and worktree locations;
- `origin` (upstream) versus `fork` (writable) remotes;
- `git fetch origin && git rebase origin/master` synchronization;
- GHCR path `ghcr.io/salja03-t21/boxes`;
- immutable SHA tag/digest release flow;
- homelab repo, stack file, server, DNS, network, and service names; and
- PR-only updates to `master`.

Add a short “Maintained fork and homelab deployment” link to `README.rst`.

**Step 4: Verify and commit**

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_container_contract.py -q
pre-commit run --all-files
git diff --check
git add .github/workflows/docker-publish.yml README.rst \
  docs/deployment/homelab.md tests/test_container_contract.py
git commit -m "ci: publish immutable amd64 images"
```

### Task 3: Review and publish the fork image

**Files:** No new source files.

**Step 1: Initialize Bouncer if needed and run it**

If `.codex/bouncer-config.md` is missing, use `bouncer-init` to create a
repo-specific configuration. Run Bouncer against the implementation plan and
the base SHA recorded before Task 1. Fix every FAIL and rerun until PASS.

**Step 2: Push and open a PR**

Use the `github:yeet` skill. Push
`feat/homelab-swarm-deployment` to the `fork` remote and open a draft PR into
`salja03-t21/boxes:master`. Include test, container smoke, and Bouncer results.

**Step 3: Make the PR reviewable and merge through the PR path**

Confirm checks pass, mark ready, and merge through GitHub. Never direct-push
to `master`.

**Step 4: Ensure Actions sees the fork workflows**

After the first fork-owned default-branch commit:

```bash
gh workflow list --repo salja03-t21/boxes
gh workflow enable docker-publish.yml --repo salja03-t21/boxes
gh workflow run docker-publish.yml --repo salja03-t21/boxes --ref master
gh run watch --repo salja03-t21/boxes --exit-status
```

If the workflow still is not registered, enable fork Actions in GitHub's
repository settings, then dispatch it again.

**Step 5: Record the immutable image**

```bash
docker buildx imagetools inspect ghcr.io/salja03-t21/boxes:sha-<short-sha>
```

Record the index digest and the `linux/amd64` manifest digest. Confirm the
package is publicly pullable without credentials before using it in Swarm.

### Task 4: Extend Open Brain Traefik into shared LAN ingress

**Files (in a new Open Brain worktree from `origin/dev`):**

- Modify: `docker-compose.yml`
- Create: `server/tests/test_lan_ingress_compose.py`
- Modify: `docs/infrastructure/docker-setup.md`

**Step 1: Create the Open Brain worktree**

Use the repo's existing `.worktrees` convention and verify it is ignored:

```bash
git fetch origin dev
git worktree add .worktrees/feat-lan-ingress \
  -b feat/lan-ingress origin/dev
```

Do not edit the detached, dirty root checkout.

**Step 2: Write failing compose-contract tests**

The test should load `docker-compose.yml` with `yaml.safe_load` and assert:

```python
def test_production_traefik_exposes_lan_http() -> None:
    traefik = compose()["services"]["traefik"]
    assert "80:3000" in traefik["ports"]
    assert "lan-ingress" in traefik["networks"]


def test_lan_ingress_is_external() -> None:
    assert compose()["networks"]["lan-ingress"] == {
        "external": True,
        "name": "lan-ingress",
    }
```

Run only this test and confirm it fails.

**Step 3: Modify the production Compose file**

Keep `3000:3000`, add `80:3000`, attach Traefik to both networks, and add:

```yaml
networks:
  lan-ingress:
    external: true
    name: lan-ingress
```

Do not change `docker-compose.test-stack.yml`; test ingress remains isolated
on port 3001.

**Step 4: Document shared ownership and safety boundary**

Document:

- `open-brain_traefik` owns the proxy process;
- `lan-ingress` is external and outlives individual stacks;
- port 3000 remains the Cloudflare/Open Brain endpoint;
- port 80 is LAN HTTP only and requires no WAN forwarding;
- other stacks must set a host rule, backend port, and
  `traefik.docker.network=lan-ingress`; and
- unknown host headers continue to hit the existing Open Brain catch-all.

**Step 5: Verify and commit**

```bash
cd server
.venv/bin/python -m pytest tests/test_lan_ingress_compose.py -q
.venv/bin/python -m pytest tests/ -x --tb=short
cd ..
docker compose -f docker-compose.yml config >/tmp/open-brain-compose.yml
git diff --check
git add docker-compose.yml server/tests/test_lan_ingress_compose.py \
  docs/infrastructure/docker-setup.md
git commit -m "feat(infra): add shared LAN ingress network"
```

**Step 6: Run Open Brain Bouncer, PR to dev, and verify test deploy**

Run the existing repo Bouncer configuration until PASS. Push the feature
branch and open a PR to `dev`. Merge through the PR path, then verify the test
environment remains healthy. This production-only Compose change should not
publish port 80 in the test stack.

**Step 7: Create the external network before production promotion**

On `10.0.5.12`:

```bash
docker network inspect lan-ingress >/dev/null 2>&1 || \
  docker network create --driver overlay --attachable lan-ingress
docker network inspect lan-ingress --format \
  'name={{.Name}} driver={{.Driver}} scope={{.Scope}} attachable={{.Attachable}}'
```

Expected: overlay, swarm scope, attachable true.

**Step 8: Promote dev to main and verify Open Brain production**

Open and merge the normal `dev -> main` production PR. Watch the deployment
workflow. Verify:

```bash
curl --fail https://mcp.ciothoughts.net/health
curl --fail http://10.0.5.12:3000/health -H 'Host: mcp.ciothoughts.net'
curl --fail http://10.0.5.12/ping
docker service inspect open-brain_traefik --format '{{json .Endpoint.Ports}}'
```

Expected: Open Brain remains healthy; Traefik publishes 3000 and 80.

### Task 5: Reconcile the homelab remote and add current Swarm documentation

**Files (in a new remote-compatible homelab worktree):**

- Modify: `README.md`
- Create: `docs/infrastructure/swarm-server.md`
- Create: `docs/services/boxes.md`
- Create: `docker_swarm/boxes/compose.yml`

**Step 1: Preserve the divergent local repository**

Record these facts in the session notes:

- local legacy main: `219b48e` at discovery;
- rewritten remote main: `c4fc8b6` at discovery;
- there is no common merge base; and
- the dirty local checkout must not be reset, cleaned, or force-pushed.

Remove only the clean worktree created by this session, then recreate the
feature branch from the rewritten `origin/main`. Do not modify the user's root
checkout.

**Step 2: Write the stack with an image placeholder test-first**

Before the compose file, create a temporary validation script or use a small
YAML contract test in `scripts/tests/test_boxes_stack.py` that asserts:

- the image contains both an immutable `sha-` tag and `@sha256:` digest;
- no service port is published;
- the external network name is `lan-ingress`;
- the host rule is exactly `boxes.ciothoughts.net`;
- the Traefik backend port is 8000; and
- one replica, healthcheck, resource limits, update rollback, and restart
  policy are present.

Then create `docker_swarm/boxes/compose.yml` using the digest captured in
Task 3:

```yaml
version: "3.8"

services:
  boxes:
    image: ghcr.io/salja03-t21/boxes:sha-<short-sha>@sha256:<index-digest>
    environment:
      STATIC_URL: /static
    networks:
      - lan-ingress
    healthcheck:
      test:
        - CMD
        - /app/env/bin/python
        - -c
        - import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=5)
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    deploy:
      replicas: 1
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 5
      update_config:
        parallelism: 1
        order: start-first
        failure_action: rollback
        monitor: 30s
      rollback_config:
        parallelism: 1
        order: stop-first
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
        reservations:
          memory: 128M
      labels:
        - traefik.enable=true
        - traefik.docker.network=lan-ingress
        - traefik.http.routers.boxes.rule=Host(`boxes.ciothoughts.net`)
        - traefik.http.routers.boxes.entrypoints=web
        - traefik.http.routers.boxes.priority=100
        - traefik.http.routers.boxes.service=boxes
        - traefik.http.services.boxes.loadbalancer.server.port=8000

networks:
  lan-ingress:
    external: true
    name: lan-ingress
```

**Step 3: Replace obsolete topology with current documentation**

`docs/infrastructure/swarm-server.md` must state:

- live node `open-brain`, address `10.0.5.12`, single manager/worker;
- Docker root, capacity snapshot, active stacks, and shared ingress network;
- `Rancher` and its multi-node PostgreSQL topology were decommissioned;
- old `docker_swarm/postgres` instructions are historical and must not be
  followed; they are intentionally absent from the rewritten remote history;
- practical inspection, deploy, verify, and rollback commands; and
- the PR-only change process.

`docs/services/boxes.md` must include source/fork paths, image pin, stack file,
DNS, ingress, deployment, SVG smoke test, update, rollback, and the LAN-only
security invariant. Link both documents from `README.md`.

**Step 4: Validate and commit**

```bash
python scripts/tests/test_boxes_stack.py
docker compose -f docker_swarm/boxes/compose.yml config >/tmp/boxes-stack.yml
git diff --check
git add README.md docs/infrastructure/swarm-server.md docs/services/boxes.md \
  docker_swarm/boxes/compose.yml scripts/tests/test_boxes_stack.py
git commit -m "feat: document and define Boxes Swarm service"
```

**Step 5: Push and open a PR; do not rewrite main**

Push the remote-compatible feature branch and open a PR to the rewritten
`main`. The PR description must explicitly say that it does not restore or
overwrite the divergent local legacy history. Merge only through the PR path.

### Task 6: Add the OPNsense internal DNS record

**Files:** No repository file; the resulting state is documented in homelab.

**Step 1: Capture the before state**

```bash
dig +short @10.0.0.1 boxes.ciothoughts.net A
dig +short @1.1.1.1 boxes.ciothoughts.net A
```

Expected before change: both empty.

**Step 2: Create the Unbound host override on the firewall**

Use the authenticated OPNsense UI or its supported API. Create exactly:

```text
Host: boxes
Domain: ciothoughts.net
Type: A
Address: 10.0.5.12
Description: LAN-only Boxes.py service on Docker Swarm
```

Apply the Unbound configuration. Do not add a public DNS record, NAT rule,
port forward, Cloudflare route, or certificate automation.

**Step 3: Verify split resolution**

```bash
dig +short @10.0.0.1 boxes.ciothoughts.net A
dig +short @1.1.1.1 boxes.ciothoughts.net A
dig +short @8.8.8.8 boxes.ciothoughts.net A
```

Expected: internal resolver returns only `10.0.5.12`; public resolvers return
nothing.

### Task 7: Deploy the Boxes stack and verify end-to-end

**Files:** No new source files unless verification uncovers a defect.

**Step 1: Preflight the live host**

```bash
ssh james@10.0.5.12 '
  docker node ls &&
  docker network inspect lan-ingress >/dev/null &&
  docker service inspect open-brain_traefik >/dev/null &&
  ! docker stack ls --format "{{.Name}}" | grep -qx boxes
'
```

Confirm port 80 belongs to Traefik and no existing `boxes` stack conflicts.

**Step 2: Deploy the reviewed homelab stack**

On the manager, use the exact compose file merged in Task 5:

```bash
docker stack deploy --with-registry-auth \
  -c docker_swarm/boxes/compose.yml boxes
```

If the GHCR package is public, registry auth is unnecessary; prefer no stored
credential. Do not build from a mutable checkout on the server.

**Step 3: Verify Swarm and Traefik**

```bash
docker stack services boxes
docker service ps boxes_boxes --no-trunc
docker service inspect boxes_boxes --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}'
docker service logs boxes_boxes --since 5m
curl --fail http://10.0.5.12/ -H 'Host: boxes.ciothoughts.net'
```

Expected: 1/1 replica, pinned digest, clean logs, HTTP 200.

**Step 4: Verify from the LAN hostname**

```bash
curl --fail http://boxes.ciothoughts.net/ >/tmp/boxes-index.html
curl --fail --get 'http://boxes.ciothoughts.net/ABox' \
  --data-urlencode 'x=100' --data-urlencode 'y=100' \
  --data-urlencode 'h=100' --data-urlencode 'render=1' \
  -o /tmp/boxes-production-smoke.svg
rg '<svg' /tmp/boxes-production-smoke.svg
```

Open the URL in a browser and visually confirm the gallery and one generated
box.

**Step 5: Reconfirm the Internet exclusion invariant**

```bash
dig +short @1.1.1.1 boxes.ciothoughts.net A
ssh james@10.0.5.12 "sudo rg -n 'boxes\.ciothoughts\.net' /etc/cloudflared || true"
```

Inspect OPNsense for no WAN NAT/port-forward to `10.0.5.12:80`. Public DNS
must remain empty and cloudflared must have no Boxes route.

**Step 6: Exercise rollback readiness without disrupting the service**

Record the current image and service spec. Verify `docker service rollback
--help` and document the exact command, but do not force a failure in the
live service. For a first-deploy rollback, `docker stack rm boxes` is valid
because the service is stateless.

**Step 7: Final Bouncer and verification pass**

Run Bouncer on every repository with code or executable deployment changes.
Treat any FAIL as blocking. Then rerun:

- Boxes full Python suite and container smoke test;
- Open Brain focused compose test and full server suite;
- homelab stack contract and `docker compose config`;
- live Swarm, DNS, HTTP, SVG, and public-exclusion checks.

Close all Beads child tasks with verification notes, close the parent, and
report IDs and final states.

### Task 8: Capture the durable handoff

**Files:**

- Modify if needed: `docs/deployment/homelab.md`
- Modify if needed: homelab `docs/services/boxes.md`

**Step 1: Replace placeholders with deployed facts**

Record final commit SHAs, image digest, PR numbers, workflow run, stack/service
names, network ID, DNS verification, and deployment date. Do not record secret
or session credential values.

**Step 2: Capture an Open Brain session summary**

Use existing tags such as `homelab`, `docker-swarm`, `deployment`,
`documentation`, `boxes`, and `session-summary`. Include what changed, why,
verification, rollback, the homelab remote-history anomaly, and the next
enhancement entry point.

**Step 3: Commit documentation updates through their feature branches**

Use intentional conventional commits and the normal PR path. Do not
direct-push either default branch.

**Step 4: Final report**

Report:

- `http://boxes.ciothoughts.net` availability and LAN-only evidence;
- fork, image, homelab, and Open Brain PR links;
- exact local and remote source locations;
- verification commands and results;
- Bouncer verdicts;
- Beads IDs and final status;
- rollback command; and
- any remaining risk or manual follow-up.
