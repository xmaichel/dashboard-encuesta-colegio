FROM python:3.12-slim

COPY cbjml-server.py /app/cbjml-server.py
COPY etl_sync.py /app/etl_sync.py
COPY Dashboard_CBJML.html /app/Dashboard_CBJML.html

WORKDIR /app

EXPOSE 8102

CMD ["python3", "-u", "cbjml-server.py"]
ENV CBJML_PORT=8102
