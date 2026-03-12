# Use the latest Amazon Linux image
FROM python:3.13-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Define env vars
# Ensure Python output is unbuffered
ENV PYTHONUNBUFFERED=1
ENV AWS_DEFAULT_REGION=us-east-1

# Install make and other build tools
RUN apt-get update && apt-get install -y --no-install-recommends make curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy Poetry configuration
COPY pyproject.toml poetry.lock* /app/

# Copy project files
COPY src /app/src
COPY tests /app/tests
COPY makefile /app/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Keep the container alive for shell interaction
CMD ["/bin/bash"]