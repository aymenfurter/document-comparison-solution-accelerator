# ============================
# Stage 1: Build the frontend
# ============================
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./ 
RUN npm install
COPY frontend/ ./
RUN npm run build

# ============================
# Stage 2: Build the backend
# ============================
FROM python:3.10-slim AS backend-builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies required by Python packages and pandoc
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev \
    build-essential \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY app /app/app

# ============================
# Stage 3: Final Image
# ============================
FROM backend-builder AS final

# Copy the built frontend files into the static directory
COPY --from=frontend-builder /frontend/dist /app/static

# Ensure proper permissions and ownership of static files
RUN chown -R root:root /app/static && \
    chmod -R 755 /app/static

# Expose the port uvicorn will run on
EXPOSE 8000

# Start uvicorn to run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
