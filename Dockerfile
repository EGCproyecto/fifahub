FROM python:3.12-slim

ARG PORT=5000
ENV PORT=${PORT}

ARG VERSION_TAG=dev
ENV VERSION_TAG=${VERSION_TAG}

# Install dependencies required for building Python packages and talking to MariaDB
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        mariadb-client \
        gcc \
        libc-dev \
        python3-dev \
        libffi-dev \
        curl \
        bash \
        openrc \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy only the folders needed to run the application
COPY app ./app
COPY core ./core
COPY migrations ./migrations
COPY scripts ./scripts
COPY rosemary ./rosemary
COPY pyproject.toml .

# Install rosemary CLI tool
RUN pip install --no-cache-dir -e .

# Ensure wait-for-db is executable when present
RUN if [ -f ./scripts/wait-for-db.sh ]; then chmod +x ./scripts/wait-for-db.sh; fi

# Expose the port (Render will set PORT; local defaults to 5000)
EXPOSE ${PORT}

ENTRYPOINT ["./scripts/wait-for-db.sh"]

# Use sh -c so ${PORT} is expanded at runtime
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} app:app --log-level info --timeout 3600"]
