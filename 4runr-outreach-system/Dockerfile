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

# Install system dependencies for runtime and Playwright
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers (using specific version from requirements)
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

# Expose port for health checks and API
EXPOSE 8080

# Health check using HTTP endpoint
HEALTHCHECK --interval=30s --timeout=5s --retries=5 --start-period=30s \
    CMD curl -fsS http://localhost:8080/health || exit 1

# Default command - start the API service
CMD ["python", "-m", "outreach.api"]