FROM ghcr.io/linuxserver/libreoffice:25.2.5

WORKDIR /app

RUN mkdir -p /app/tmp

RUN apk add --no-cache \
        supervisor \
        python3 \
        libreoffice-sdk \
        curl

COPY ./server.py /app/server.py
COPY ./supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY ./supervisor_pair_listener.py /app/supervisor_pair_listener.py
COPY ./watchdog.py /app/watchdog.py

RUN chmod +x /app/server.py
RUN chmod +x /app/supervisor_pair_listener.py
RUN chmod +x /app/watchdog.py

# Create supervisor log directory
RUN mkdir -p /var/log/supervisor

EXPOSE 8080

# Ensure our supervisord is the only init (override base entrypoint)
ENTRYPOINT ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

