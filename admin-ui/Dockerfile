FROM node:24.14.0-bookworm-slim AS builder

WORKDIR /build

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
COPY frontend/vite.config.ts ./frontend/
COPY frontend/index.html ./frontend/

COPY core/src/ ./core/src/
COPY backend/src/ ./backend/src/
COPY frontend/src/ ./frontend/src/
RUN npm run build


FROM node:24.14.0-bookworm-slim AS the-backend

WORKDIR /app

COPY --from=builder /build/backend/dist/ .

EXPOSE 3000

CMD ["node", "index.cjs"]


FROM nginx:1.29.6-alpine3.23 AS the-frontend

COPY --from=builder /build/frontend/dist/ /usr/share/nginx/html
