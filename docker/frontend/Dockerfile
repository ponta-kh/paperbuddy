FROM node:26-bookworm-slim

ENV PNPM_HOME=/pnpm \
    PATH=/pnpm:$PATH

WORKDIR /app

RUN corepack enable

COPY pnpm-lock.yaml pnpm-workspace.yaml ./
COPY frontend/package.json frontend/package.json
COPY infra/package.json infra/package.json

RUN pnpm install --filter frontend --frozen-lockfile

COPY frontend frontend

WORKDIR /app/frontend

EXPOSE 5173

CMD ["pnpm", "dev", "--", "--host", "0.0.0.0"]
