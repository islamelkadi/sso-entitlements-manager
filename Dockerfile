FROM python:3.13-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    AWS_DEFAULT_REGION=us-east-1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME=/opt/poetry

RUN apt-get update && apt-get install -y --no-install-recommends \
    make \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN curl --silent --show-error --location https://install.python-poetry.org | python3 -

ENV PATH="${POETRY_HOME}/bin:${PATH}"

# Copy just the dependency files first for better caching
COPY pyproject.toml poetry.lock* ./

# Copy the source code and tests
COPY src/ src/
COPY tests/ tests/

RUN poetry install --no-interaction --with dev

CMD ["/bin/bash"]