ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.19
FROM ${BUILD_FROM}

RUN apk add --no-cache python3 py3-pip

COPY app /app

RUN pip3 install --no-cache-dir --break-system-packages -r /app/requirements.txt

COPY rootfs /

RUN chmod a+x /etc/services.d/streamio_notifications/run \
    && chmod a+x /etc/services.d/streamio_notifications/finish
