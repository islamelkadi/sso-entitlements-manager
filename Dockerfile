# Use the latest Amazon Linux image
FROM python:3.13-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Define env vars
# Ensure Python output is unbuffered
ENV PYTHONUNBUFFERED=1
ENV AWS_DEFAULT_REGION=us-east-1

# Install make and other build tools
RUN apt-get update && apt-get install -y --no-install-recommends make \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy over files to the container
COPY pyproject.toml makefile /app/
COPY src /app/src
COPY tests /app/tests

# Install pip packages
RUN pip3 install --upgrade pip
RUN pip3 install .[dev]

# Keep the container alive for shell interaction
CMD ["/bin/bash"]