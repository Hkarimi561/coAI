FROM node:20-alpine AS deps
WORKDIR /app
# Set NPM_REGISTRY in .env if registry.npmjs.org is unreachable (company mirror)
ARG NPM_REGISTRY=
RUN if [ -n "$NPM_REGISTRY" ]; then npm config set registry "$NPM_REGISTRY"; fi     && npm config set fetch-retries 6 && npm config set fetch-timeout 180000
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

FROM node:20-alpine AS build
WORKDIR /app
# Where the Next.js server proxies /api/* to (baked in at build time).
ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=${BACKEND_URL} NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS run
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]
