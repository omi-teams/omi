---
id: docker
summary: Dockerfile and compose: image size, user, secrets, pinning
applies: **/Dockerfile*, docker/**, **/compose*.yml
---
# docker

- Pin base image tags (a digest for release images); never `latest`.
- Run as a non-root `USER`; do not add capabilities or mount the Docker socket.
- Order layers by change rate: dependencies first, source last; add a `.dockerignore`.
- Multi-stage builds: keep compilers and caches out of the final image.
- No secrets in `ARG`, `ENV` or layers; pass them at run time.
- Add a `HEALTHCHECK`; use exec-form `CMD` and `ENTRYPOINT`.
