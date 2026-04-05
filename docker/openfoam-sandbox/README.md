# OpenFOAM Sandbox Image

This directory defines the project-local DeerFlow sandbox image used for submarine CFD work.

The image extends the standard DeerFlow/Agent Infra sandbox base and installs OpenFOAM 13 so that
DeerFlow tools can run `simpleFoam`, `blockMesh`, and `snappyHexMesh` inside the sandbox runtime.

In the VibeCFD architecture, this image is a hard execution boundary:

- the lead agent may decide whether execution is warranted
- the actual OpenFOAM commands still run inside the sandbox
- reviewable manifests, logs, and reports must be emitted as artifacts
- server deployment should rely on this boundary instead of trusting prompt-only rules

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

## Safety Notes

- Treat sandboxed execution as mandatory for risky CFD commands in server environments.
- Keep generated case scaffolds under DeerFlow `workspace` and reviewable outputs under DeerFlow `outputs`.
- Do not treat the sandbox as a workflow engine; it is the execution isolation layer for the lead agent and domain tools.
