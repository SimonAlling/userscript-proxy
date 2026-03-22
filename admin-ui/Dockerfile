FROM node:24.14.0-bookworm-slim AS builder

WORKDIR /build

ARG BACKEND_HOST=localhost
ARG BACKEND_PORT=3000

COPY package.json package-lock.json ./
COPY core/package.json ./core/
COPY backend/package.json ./backend/
COPY frontend/package.json ./frontend/
RUN npm ci --no-audit --no-fund

COPY tsconfig.base.json ./
COPY core/tsconfig.json ./core/
COPY backend/tsconfig.json ./backend/
COPY frontend/tsconfig.json ./frontend/
COPY frontend/tsconfig.app.json ./frontend/
COPY frontend/tsconfig.node.json ./frontend/
COPY eslint.config.js ./
COPY frontend/vite.config.ts ./frontend/
COPY frontend/index.html ./frontend/

COPY core/src/ ./core/src/
COPY backend/src/ ./backend/src/
COPY frontend/src/ ./frontend/src/
RUN npm run build
RUN npm run lint


FROM node:24.14.0-bookworm-slim AS runtime

WORKDIR /app

ENV FRONTEND_DIR=/app/public

COPY --from=builder /build/backend/dist/ .
COPY --from=builder /build/frontend/dist/ ${FRONTEND_DIR:?}

EXPOSE $BACKEND_PORT

CMD ["node", "index.cjs"]
