FROM python:3
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --no-cache-dir

COPY src src
COPY templates templates
COPY static static

# Run sanic in production mode
ENV APP_DEBUG false

EXPOSE 8000
ENTRYPOINT [ "python3", "-m", "src.main" ]
