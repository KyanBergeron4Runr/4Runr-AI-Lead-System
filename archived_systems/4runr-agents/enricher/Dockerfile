FROM python:3.11-slim AS build

WORKDIR /app

# Install build dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim AS production

WORKDIR /app

# Copy only the necessary files from the build stage
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY app.py .

# Create shared directory
RUN mkdir -p /shared

# Create logs directory
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ENRICHER_DELAY_SECONDS=60

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import os; exit(0 if os.path.exists('/shared') else 1)" || exit 1

# Run the application
CMD ["python", "app.py"]