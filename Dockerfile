FROM ubuntu:20.04

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
  apt-get install -y wget python3 python3-pip supervisor && \
  rm -rf /var/lib/apt/lists/*

RUN wget -O caddy "https://caddyserver.com/api/download?os=linux&arch=amd64" && chmod +x caddy

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --no-cache-dir

COPY src src
# /static will be served by caddy
RUN mkdir public && mv src/static public/static

COPY hypercorn.toml .
COPY Caddyfile Caddyfile
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 80
CMD [ "/usr/bin/supervisord" ]
