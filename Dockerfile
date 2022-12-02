FROM python:3.10-slim
WORKDIR /app/

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src src
COPY templates templates
COPY static static

ENV APP_DEBUG=false
EXPOSE 8000
ENTRYPOINT [ "python3", "-m", "src.main" ]
