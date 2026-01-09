FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (including LiveKit requirements)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libglib2.0-0 \
    libgobject-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml README.md ./

# Install dependencies using uv
RUN uv pip install --system .

# Copy source code
COPY src/ src/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
