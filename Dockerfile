FROM python:3.12-slim

WORKDIR /app
COPY cbjml-server.py etl_sync.py Dashboard_CBJML.html dashboard_runtime.js ./
ENV CBJML_ROOT=/app \
    CBJML_PORT=8102 \
    PYTHONUNBUFFERED=1
EXPOSE 8102
CMD ["python3", "-u", "cbjml-server.py"]
