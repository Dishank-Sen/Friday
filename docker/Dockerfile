FROM lscr.io/linuxserver/webtop:ubuntu-xfce

USER root

COPY server/requirements.txt /tmp/requirements.txt

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
        python3-venv \
        scrot \
        xdotool \
    && python3 -m venv /opt/friday/venv \
    && /opt/friday/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -rf /var/lib/apt/lists/* /tmp/requirements.txt

COPY server /opt/friday/server
COPY src/friday /opt/friday/friday
COPY docker/rootfs/ /

RUN chmod +x /custom-services.d/friday-control

ENV DISPLAY=:1
ENV PYTHONPATH=/opt/friday

EXPOSE 8000
