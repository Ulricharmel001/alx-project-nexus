FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
        gcc \
        build-essential \
        libpq-dev \
        default-libmysqlclient-dev \
        pkg-config \
        && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Expose port
EXPOSE 8000

# Entrypoint
CMD ["bash", "entrypoint.sh"]
