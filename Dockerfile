FROM python:3.11-slim-bookworm AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends git build-essential libjpeg-dev libtiff-dev libffi-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.11-slim-bookworm
LABEL description="Discord label printing bot"
WORKDIR /app
ENV PYTHONUNBUFFERED=1 DATABASE_PATH=/data/database.sqlite
RUN apt-get update && apt-get install -y --no-install-recommends \
    restic openssh-client sshpass \
    libpango-1.0-0 libpangoft2-1.0-0 libusb-1.0-0 \
    fonts-dejavu fonts-liberation fonts-freefont-ttf fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --no-deps /wheels/*.whl \
    && rm -rf /wheels && mkdir /data
COPY docker/entrypoint.py /opt/labelbot/
COPY src/labelbot/backup/ssh_config /etc/ssh/ssh_config.d/backup.conf
ENTRYPOINT ["python", "/opt/labelbot/entrypoint.py"]
