# ─────────────────────────────────────────────────────────────────────
# MindFlow / Rovot Frontend — Production Docker Image
# Multi-stage build: Node.js for building, Nginx for serving.
# ─────────────────────────────────────────────────────────────────────

# Stage 1: Build
FROM node:22-alpine AS builder

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy package files first for better caching
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile 2>/dev/null || pnpm install

# Copy source and build
COPY . .

# Build-time environment variables
ARG VITE_API_URL=http://localhost:5000/api
ENV VITE_API_URL=${VITE_API_URL}

RUN pnpm build

# Stage 2: Serve with Nginx
FROM nginx:alpine AS runtime

# Security: remove default config
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Custom Nginx config for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Security headers
RUN echo 'server_tokens off;' > /etc/nginx/conf.d/security.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
