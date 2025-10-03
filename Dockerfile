# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy project files
COPY pyproject.toml ./

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -e .

# Copy application code
COPY agent_ethan2/ ./agent_ethan2/
COPY schemas/ ./schemas/
COPY docs/ ./docs/
COPY README.md ./

# Create a non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Default command
CMD ["python", "-m", "agent_ethan2"]

