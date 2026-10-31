FROM node:24.11.0-trixie-slim
# Python 3.13 (trixie) and git for project tests; add your project's toolchain here (omi worker rebuilds when this file changes)
# git is for read-only use: /work/.git is a ro bind and its gitdir points to a host path that does not exist here
RUN apt-get update && apt-get install -y --no-install-recommends python3 git ca-certificates && rm -rf /var/lib/apt/lists/*
# CLI baked into the image (not on a noexec tmpfs, avoids exit 126)
RUN npm i -g @anthropic-ai/claude-code@2.1.302 && npm cache clean --force
RUN npm i -g @openai/codex@0.164.0 && npm cache clean --force
# Toolchain example (uncomment and adapt; TASK-001 of a new project adds the chosen stack here and its registries to "network_allow" in .omi/config.json):
# RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xz
# ENV PATH=/usr/local/go/bin:$PATH
# Browser QA (opt-in: uncomment this block for projects with browser tests).
# Headless Chromium only; measure image size before/after enabling this block.
# ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
# ENV NODE_PATH=/usr/local/lib/node_modules
# ENV OMI_BROWSER_REQUIRED=1
# RUN npm install -g playwright@1.56.1 && playwright install --with-deps --only-shell chromium \
#     && chmod -R a+rX /opt/ms-playwright && npm cache clean --force && rm -rf /var/lib/apt/lists/*
# keep ENV PATH lines above this one; login shells (bash -lc) reset PATH from /etc/profile; keep the image PATH (incl. later ENV PATH entries)
RUN printf 'export PATH="%s"\n' "$PATH" > /etc/profile.d/omi-path.sh
USER node
WORKDIR /work
