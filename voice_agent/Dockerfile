FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml README.md ./

# Install dependencies using uv
# Note: Installing directly into system python for simplicity in container
RUN uv pip install --system .

# Pre-download Silero VAD model during build (caches in image)
# This prevents runtime download delays
# VAD.load() is synchronous and returns a VAD object directly
RUN python -c "from livekit.plugins import silero; silero.VAD.load()"

# Copy source code
COPY src/ src/

# Run the worker
CMD ["python", "-m", "src.main", "start"]
