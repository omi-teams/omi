FROM node:24.11.0-trixie-slim
# Python 3.13 (trixie) and git for project tests; add your project's toolchain here (omi worker rebuilds when this file changes)
# git is for read-only use: /work/.git is a ro bind and its gitdir points to a host path that does not exist here
RUN apt-get update && apt-get install -y --no-install-recommends python3 git && rm -rf /var/lib/apt/lists/*
# CLI baked into the image (not on a noexec tmpfs, avoids exit 126)
RUN npm i -g @anthropic-ai/claude-code@2.1.302 && npm cache clean --force
USER node
WORKDIR /work
