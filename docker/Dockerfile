FROM node:24-slim
# CLI baked into the image (not on a noexec tmpfs, avoids exit 126)
RUN npm i -g @anthropic-ai/claude-code@2.1.302 && npm cache clean --force
USER node
WORKDIR /work
