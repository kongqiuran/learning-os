FROM python:3.13.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    API_RELOAD=false \
    LEARNING_OS_DATA_DIR=/data \
    DATABASE_URL=sqlite:////data/database/learning_os.db

WORKDIR /app

RUN groupadd --system learningos \
    && useradd --system --gid learningos --home-dir /app learningos

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY api_server.py ./
COPY worker.py ./
COPY src ./src
COPY scripts ./scripts

RUN mkdir -p /data/database /data/uploads \
    && chown -R learningos:learningos /app /data

USER learningos

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3).read()"]

CMD ["python", "api_server.py"]
