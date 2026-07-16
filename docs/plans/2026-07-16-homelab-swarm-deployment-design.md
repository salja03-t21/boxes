# Boxes.py Homelab Swarm Deployment Design

## Goal

Run Boxes.py as a reproducible, LAN-only service on the existing single-node
Docker Swarm at `10.0.5.12`, reachable as
`http://boxes.ciothoughts.net`, while leaving a clean source, deployment, and
documentation path for later application enhancements.

## Confirmed constraints

- The application is intentionally unauthenticated.
- It must be reachable from the trusted LAN only.
- It must not receive a public DNS record, Cloudflare Tunnel route, WAN port
  forward, or other Internet ingress.
- The existing Traefik service on `10.0.5.12` should provide the clean URL.
- OPNsense Unbound should own the internal DNS record.
- The obsolete `Rancher` Swarm topology is decommissioned and must not remain
  as active operational guidance.
- Future application work will be maintained in the public fork
  `salja03-t21/boxes`, with upstream retained as a synchronization remote.

## Current state

The live host is `open-brain` at `10.0.5.12`. It is the leader and only node
in its Swarm. At discovery time it had 10 CPUs, about 64 GiB RAM, and 283 GiB
free disk. It runs the `open-brain` and `open-brain-test` stacks.

The existing production Traefik service:

- watches Swarm service labels globally;
- listens on container port `3000` and publishes host port `3000`;
- is attached only to the stack-scoped `open-brain_internal` overlay;
- uses `exposedByDefault=false`; and
- is the endpoint used by the existing Open Brain Cloudflare Tunnel.

Boxes.py is stateless. Its upstream repository already contains a Gunicorn
container definition and publishes a `linux/amd64` GHCR image. The current
Dockerfile fetches the upstream Git repository during the build, however, so
it cannot faithfully package changes in the checked-out fork. That must be
corrected before the fork becomes the deployment image source.

The local homelab repository contains a 2023 `Rancher`/multi-node PostgreSQL
example that no longer describes any live infrastructure. Its remote `main`
was also force-rewritten to an unrelated new initial commit during discovery.
No direct push to either version of `main` is allowed; remote-history
reconciliation must remain a reviewed PR decision.

## Approaches considered

### 1. Reuse Traefik through a shared ingress overlay — selected

Add a durable external overlay named `lan-ingress`, attach the existing
Traefik service and Boxes.py to it, publish port `80` from Traefik, and route
requests by the `boxes.ciothoughts.net` host header.

This avoids another reverse proxy, gives the service a clean URL, and creates
a reusable path for later LAN applications. It requires a small reviewed
change to the Open Brain stack because that repository currently owns the
Traefik service.

### 2. Run a second LAN-only reverse proxy

A separate Traefik or Caddy stack would provide clearer lifecycle ownership,
but it would duplicate proxy software and configuration on a single-node
homelab. The extra isolation is not worth the added operational surface yet.

### 3. Publish Boxes.py directly

Publishing `4455:8000` is the smallest deployment change, but the result is a
port-qualified URL and no reusable ingress convention. This was rejected in
favor of the shared proxy.

## Architecture

```text
LAN client
   |
   | DNS: boxes.ciothoughts.net -> 10.0.5.12
   v
OPNsense Unbound
   |
   | HTTP :80 (LAN; no WAN forwarding)
   v
open-brain_traefik
   |
   | Host("boxes.ciothoughts.net") over lan-ingress
   v
boxes_boxes:8000
```

The `lan-ingress` network is external to both stacks so neither stack owns or
deletes it. Boxes.py does not join `open-brain_internal`; Open Brain's private
services remain isolated. Traefik retains port `3000` so the existing
Cloudflare/Open Brain path does not move.

## Repository responsibilities

### `salja03-t21/boxes`

- Build the container from the checked-out source rather than fetching
  `florianfesti/boxes` during the image build.
- Keep local development Compose behavior separate from production Swarm
  configuration.
- Publish a `linux/amd64` image to GHCR with an immutable commit-derived tag
  and digest.
- Run existing Python checks plus a container smoke test before publishing.
- Document upstream synchronization, image publication, and the relationship
  to the homelab deployment repository.

### `salja03-t21/homelab`

- Own the Boxes.py Swarm stack specification and operations runbook.
- Pin the application image by immutable digest; do not deploy `latest` or a
  floating branch tag.
- Record the actual single-node Swarm topology at `10.0.5.12`.
- Remove or clearly archive the decommissioned `Rancher` PostgreSQL example.
- Document deployment, verification, update, rollback, DNS, and the
  no-Internet invariant.

Because the remote history was force-rewritten, the implementation must first
choose a PR-safe reconciliation path. The recommended path is a fresh branch
from the rewritten remote `main` containing only current, reviewed
infrastructure documentation and the new stack. The richer local history is
preserved locally and must not be force-pushed over the remote.

### `salja03-t21/open-brain`

- Keep ownership of the existing Traefik service.
- Add host port `80` while retaining `3000`.
- Attach Traefik to the external `lan-ingress` overlay.
- Preserve existing Open Brain routes, middleware, Cloudflare behavior, and
  test-stack isolation.
- Document that this Traefik instance also serves as the shared LAN ingress.

## Boxes.py service specification

The homelab stack will define one replicated service with:

- one replica on the single-node Swarm;
- no published ports of its own;
- the external `lan-ingress` overlay;
- a Traefik router restricted to `Host("boxes.ciothoughts.net")` on the
  existing `web` entrypoint;
- an explicit Traefik backend port of `8000` and network of `lan-ingress`;
- an application health check using Python's standard library against the
  local HTTP server;
- restart-on-failure behavior;
- rolling update and automatic rollback settings; and
- conservative CPU and memory limits, adjustable after measurement.

The application has no persistent data or secrets. No NFS mount, Docker
secret, Doppler project, or database is needed.

## DNS and network boundary

OPNsense Unbound will receive a host override:

```text
Host: boxes
Domain: ciothoughts.net
Address: 10.0.5.12
```

The deployment is LAN-only because:

- Unbound is the only DNS source for the record;
- no public DNS record is created;
- no Cloudflare Tunnel ingress is created;
- Boxes.py publishes no Swarm port;
- Traefik port `80` is reachable on the LAN, with no OPNsense WAN port
  forwarding rule; and
- the runbook includes checks for both internal resolution and absence of
  public resolution.

Publishing port `80` also makes the existing Traefik entrypoint reachable on
the LAN. The Boxes router's host-specific rule and higher priority ensure
`boxes.ciothoughts.net` reaches Boxes.py. The existing Open Brain catch-all
behavior for other host headers is unchanged and should be documented as an
accepted property of reusing its proxy.

## Deployment flow

1. Merge the container-readiness changes through a PR in the Boxes fork.
2. Let CI build and publish the immutable GHCR image; record its digest.
3. Create the external `lan-ingress` overlay once on the Swarm manager.
4. Merge and deploy the reviewed Open Brain Traefik change, verifying Open
   Brain before continuing.
5. Add the OPNsense Unbound host override and verify LAN-only resolution.
6. Merge the homelab stack pin and deploy it as stack `boxes`.
7. Verify service health, routing, SVG generation, image digest, and Internet
   exclusion.

Normal application updates build a new immutable fork image, then update only
the pinned digest in the homelab stack through a PR. The stack deployment is
the release boundary.

## Verification

Verification must cover:

- existing Boxes.py tests and pre-commit checks;
- successful `linux/amd64` container build;
- container health and a generated SVG smoke test;
- `docker service ls` and `docker service ps` showing a healthy task;
- Traefik routing by the exact host header;
- `boxes.ciothoughts.net` resolving to `10.0.5.12` through OPNsense;
- the hostname not resolving through a public recursive resolver;
- no Cloudflare ingress or WAN port-forward for Boxes.py;
- Open Brain remaining healthy through its existing port `3000` path after
  Traefik changes; and
- rollback to the prior image digest and prior Traefik service specification.

## Rollback

- Boxes.py: restore the prior pinned digest and redeploy the `boxes` stack, or
  remove the stateless stack if this is the first release.
- Traefik: restore the prior Open Brain stack specification; port `3000`
  remains the unchanged production path throughout.
- DNS: remove the Unbound host override and apply/reload the resolver.
- Network: remove `lan-ingress` only after no services are attached.

## Enhancement handoff

After the deployment is verified, enhancements begin from the fork's current
default branch in a new feature branch/worktree. The deployment runbook will
identify:

- local checkout and fork URLs;
- upstream synchronization commands;
- image workflow and registry path;
- homelab stack and runbook paths;
- live host, DNS name, overlay, service, and stack names;
- validation commands; and
- the PR-only release sequence.

This makes later generator or web-interface changes application work rather
than another infrastructure-discovery exercise.
