# OpenFOAM Sandbox Image

This directory defines the project-local DeerFlow sandbox image used for submarine CFD work.

The image extends the standard DeerFlow/Agent Infra sandbox base and installs OpenFOAM 13 so that
DeerFlow tools can run `simpleFoam`, `blockMesh`, and `snappyHexMesh` inside the sandbox runtime.

## Build

```bash
docker build \
  -t deer-flow-openfoam-sandbox:latest \
  -f docker/openfoam-sandbox/Dockerfile \
  docker/openfoam-sandbox
```

If the default sandbox registry is slow or inaccessible, override the base image:

```bash
docker build \
  --build-arg BASE_IMAGE=ghcr.io/agent-infra/sandbox:latest \
  -t deer-flow-openfoam-sandbox:latest \
  -f docker/openfoam-sandbox/Dockerfile \
  docker/openfoam-sandbox
```

## Verify

```bash
docker run --rm deer-flow-openfoam-sandbox:latest bash -lc "foamVersion && simpleFoam -help | head -5"
```

## DeerFlow Config

Use this image from `config.yaml`:

```yaml
sandbox:
  use: deerflow.community.aio_sandbox:AioSandboxProvider
  image: deer-flow-openfoam-sandbox:latest
  environment:
    DEER_FLOW_RUNTIME_PROFILE: local_cli
```

## Runtime Profile Vocabulary

Use the same `DEER_FLOW_RUNTIME_PROFILE` value across local runs, Docker Compose, and deployed environments so provenance parity stays honest in solver dispatch and result reporting.

- `local_cli`: local Codex or CLI-driven runs outside Docker Compose
- `docker_compose_dev`: the development stack from `docker/docker-compose-dev.yaml`
- `docker_compose_deployed`: the deployed stack from `docker/docker-compose.yaml`
