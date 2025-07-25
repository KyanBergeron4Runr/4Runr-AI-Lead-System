FROM python:3.11-slim AS build

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install build dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Production stage
FROM python:3.11-slim AS production

WORKDIR /app

# Install system dependencies for Playwright runtime
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages and Playwright browsers from build stage
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /root/.cache/ms-playwright /root/.cache/ms-playwright

# Copy application files
COPY app.py .
COPY linkedin_scraper.py .

# Create shared directory
RUN mkdir -p /shared

# Create logs directory
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import os; exit(0 if os.path.exists('/shared') else 1)" || exit 1

# Run the application
CMD ["python", "app.py"]