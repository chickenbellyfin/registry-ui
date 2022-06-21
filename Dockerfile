# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Builder Image
#
FROM python:3-alpine AS builder

ENV PATH="/app/venv/bin:$PATH"

WORKDIR /app/

COPY requirements.txt requirements.txt

RUN \
    echo "**** Install build packages. ****" && \
        apk --no-cache upgrade && \
        apk add --no-cache \
            gcc \
            musl-dev \
            python3-dev \
            alpine-sdk \
            libffi-dev && \
    echo "**** Build registry ui ****" && \
        python3 -m venv --clear venv && \
        pip install -r requirements.txt --no-cache-dir

COPY src src
COPY templates templates
COPY static static

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Runtime Image
#
FROM python:3-alpine AS final

COPY --from=builder /app /app

WORKDIR /app/

ENV \
    PATH="/app/venv/bin:$PATH" \
    APP_DEBUG=false

EXPOSE 8000

ENTRYPOINT [ "python3", "-m", "src.main" ]