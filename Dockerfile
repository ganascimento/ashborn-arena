FROM python:3.11-slim AS backend

WORKDIR /app

COPY pyproject.toml ./
COPY engine/ engine/
COPY backend/ backend/
COPY training/ training/

RUN pip install --no-cache-dir .

RUN mkdir -p models/easy models/normal models/hard
COPY models/ models/

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM node:18-alpine AS frontend-build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ .
RUN npm run build


FROM nginx:alpine AS frontend

COPY --from=frontend-build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
