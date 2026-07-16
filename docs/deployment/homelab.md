# Boxes.py homelab deployment

This fork packages the checked-out Boxes.py source for the private homelab
service at `http://boxes.ciothoughts.net`. The application has no
authentication, so the hostname and Traefik entrypoint must remain reachable
from the LAN only. Do not add this hostname to public DNS or to the existing
Cloudflare Tunnel.

## Ownership and locations

| Item | Location or name |
| --- | --- |
| Maintained fork | <https://github.com/salja03-t21/boxes> |
| Upstream project | <https://github.com/florianfesti/boxes> |
| Local source checkout | `/Users/jamessalmon/Repositories/boxes/boxes` |
| Feature worktrees | `~/.config/superpowers/worktrees/boxes/` |
| Homelab repository | `/Users/jamessalmon/Repositories/homelab` |
| Homelab stack file | `docker_swarm/boxes/compose.yml` |
| Swarm manager | `james@10.0.5.12` (`open-brain`) |
| Image | `ghcr.io/salja03-t21/boxes` |
| Stack / service | `boxes` / `boxes_web` |
| Shared ingress network | `lan-ingress` |
| Internal DNS name | `boxes.ciothoughts.net` |
| Internal DNS resolver | OPNsense at `10.0.0.1` |

The local Git remotes deliberately have different roles:

- `origin` is the read-only upstream project, `florianfesti/boxes`.
- `fork` is the writable maintained fork, `salja03-t21/boxes`.

Confirm these before pushing with `git remote -v`. All changes to the fork's
`master` branch go through a pull request; do not push directly to `master`.

## Source and enhancement workflow

The web application lives in `boxes/scripts/boxesserver.py`. Generators and
shared geometry code live under `boxes/`, static web assets under `static/`,
and container packaging under `scripts/Dockerfile`. The local developer stack
is `docker-compose.yml`; deployment configuration is owned by the separate
homelab repository.

For an enhancement:

1. Fetch both remotes and create a named feature branch/worktree from the
   maintained fork's `master`.
2. Add a failing test before changing behavior. Container invariants belong in
   `tests/test_container_contract.py`; application behavior belongs in the
   existing Python test suite.
3. Run the focused tests, then `.venv/bin/pytest -q` and the repository's
   pre-commit checks.
4. Run Bouncer at the completed implementation milestone.
5. Push the feature branch to `fork` and merge it to `master` through a pull
   request.
6. Promote the resulting immutable image digest through a separate homelab
   pull request.

To bring upstream changes into a dedicated synchronization branch:

```bash
git fetch origin
git fetch fork
git rebase origin/master
```

Resolve and test the synchronization branch, then open a PR to the fork's
`master`. Never rewrite the fork's shared `master` history.

## Image release contract

`.github/workflows/docker-publish.yml` builds `linux/amd64`, matching the
Swarm node. Pull requests build without pushing. A merge to `master`, a manual
dispatch, or a release tag publishes a signed image to GHCR. Every published
commit receives a `sha-<short-sha>` tag.

Treat the tag as a lookup aid, not a deployment pin. Record the manifest
digest produced by GitHub Actions and set the homelab stack image to:

```text
ghcr.io/salja03-t21/boxes@sha256:<manifest-digest>
```

This keeps rollback deterministic even if a tag is moved. The GHCR package
must remain publicly pullable because the Swarm currently pulls without
registry credentials; public image availability does not expose the running
application to the Internet.

## Network path and isolation

The request path is:

```text
LAN client -> OPNsense DNS -> 10.0.5.12:80 -> Open Brain Traefik
           -> lan-ingress overlay -> boxes_web:8000
```

The Boxes stack publishes no host port. Swarm labels select
`Host("boxes.ciothoughts.net")`, the `web` Traefik entrypoint, backend port
`8000`, and Docker network `lan-ingress`. The existing Open Brain Traefik
service owns LAN port 80 and joins the same external overlay.

LAN-only protection has three independent checks:

- OPNsense provides an internal host override for `boxes.ciothoughts.net` to
  `10.0.5.12`.
- Public DNS has no record for the hostname.
- No Cloudflare Tunnel route or Internet-facing firewall rule targets Boxes.

Changing DNS alone is not sufficient authorization to expose the service.

## Deployment and rollback ownership

The homelab repository is the deployment source of truth. Its Boxes service
runbook contains the exact preflight, deployment, verification, and rollback
commands. At a high level, promotion means updating only the image digest,
validating the rendered Compose file, merging the homelab PR, and deploying
the `boxes` stack from the Swarm manager.

Rollback is the inverse: restore the previous known-good digest in a homelab
PR and redeploy. Removing the stack must not remove `lan-ingress`, because the
network is shared with Traefik and outlives either stack.
