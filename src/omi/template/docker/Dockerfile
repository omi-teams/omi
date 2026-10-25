FROM node:24-slim
# Python 3 for project tests; add your project's toolchain here (omi worker rebuilds when this file changes)
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
# CLI baked into the image (not on a noexec tmpfs, avoids exit 126)
RUN npm i -g @anthropic-ai/claude-code@2.1.302 && npm cache clean --force
USER node
WORKDIR /work
