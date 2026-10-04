FROM node:22-bookworm-slim AS frontend-builder
WORKDIR /app
COPY frontend/package.json frontend/package.json
RUN npm --prefix frontend install --no-audit --no-fund
COPY frontend frontend
RUN npm --prefix frontend run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PORT=3000
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend backend
COPY public public
COPY app.config.ts package.json README.md ./
COPY --from=frontend-builder /app/frontend/dist frontend/dist
EXPOSE 3000
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-3000}"]
