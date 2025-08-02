# Multi-stage Dockerfile for 4Runr Autonomous Outreach System

# Build stage
FROM python:3.11-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Install system dependencies for runtime
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers
RUN pip install playwright==1.40.0 && \
    playwright install chromium && \
    playwright install-deps chromium

# Create non-root user
RUN useradd --create-home --shell /bin/bash outreach

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/outreach/.local

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs && chown -R outreach:outreach /app

# Switch to non-root user
USER outreach

# Add local Python packages to PATH
ENV PATH=/home/outreach/.local/bin:$PATH

# Set Python path
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from shared.config import config; print('OK')" || exit 1

# Default command
CMD ["python", "run_outreach_pipeline.py"]