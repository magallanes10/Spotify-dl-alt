FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg curl && \
    pip install spotdl && \
    mkdir -p downloads

COPY . .

CMD ["python", "main.py"]
