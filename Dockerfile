FROM python:3
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt --no-cache-dir

EXPOSE 5000
ENTRYPOINT [ "python3", "-m", "src.main" ]