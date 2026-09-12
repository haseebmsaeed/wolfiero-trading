FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration and source
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

# Non-root user
RUN useradd -m -u 1001 agent
USER agent

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=30s \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port for agent server
EXPOSE 8001

# Run agent
CMD ["python", "-m", "agent.server"]
