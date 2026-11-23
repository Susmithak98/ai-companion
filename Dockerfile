# Aira API service image (text chat over HTTP; voice mode runs locally)
FROM python:3.12-slim AS base
LABEL org.opencontainers.image.source="https://github.com/Susmithak98/ai-companion"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    AIRA_DATA_DIR=/data AIRA_LOG_JSON=true
WORKDIR /app
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt
COPY config.py logging_setup.py storage.py agents.py api.py ./
COPY core/ core/
RUN useradd --create-home --uid 10001 aira && mkdir -p /data && chown aira /data
USER aira
VOLUME ["/data"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
