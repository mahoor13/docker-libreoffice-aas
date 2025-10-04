FROM linuxserver/libreoffice:25.2.5

WORKDIR /app

RUN mkdir -p /app/tmp

COPY ./server.py /app/server.py
COPY ./supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN chmod +x /app/server.py

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        supervisor \
        libreoffice-script-provider-python \
        python3-uno \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Create supervisor log directory
RUN mkdir -p /var/log/supervisor

EXPOSE 8080

# Start supervisor to manage both processes
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

