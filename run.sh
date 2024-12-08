#!/usr/bin/env bash
set -euo pipefail

# Build the Docker image
docker build -t my-doc-compare-api:latest .

# Run the container using environment variables from .env
docker run --env-file .env -p 8000:8000 my-doc-compare-api:latest