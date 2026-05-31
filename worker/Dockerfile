FROM python:3.12-slim

WORKDIR /app

# Day 5: add this line for FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Worker shares task definitions with backend
COPY ../backend/tasks ./tasks
COPY ../backend/services ./services
COPY ../backend/logger.py ./logger.py

CMD ["celery", "-A", "tasks.celery_app.celery", "worker", "--loglevel=info", "--concurrency=2"]