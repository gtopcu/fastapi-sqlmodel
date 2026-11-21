FROM python:3.14-slim

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Configure environment:
# - UV_COMPILE_BYTECODE: Compile Python source files to bytecode for faster startup
# - PYTHONUNBUFFERED: Ensure logs appear immediately
# - PATH: Ensure the virtualenv's binaries are used by default
ENV UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock* .python-version ./

# Install dependencies without installing the project itself
RUN uv sync --frozen --no-install-project

# Copy the rest of the application code
COPY . .

# Finalize project install
RUN uv sync --frozen

# Expose FastAPI default port
EXPOSE 8000

# Run FastAPI via uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
