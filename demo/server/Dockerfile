FROM python:3.12-slim

RUN groupadd -r adhp && useradd -r -g adhp -d /app -s /sbin/nologin adhp

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY adhp-config.json .

RUN chown -R adhp:adhp /app

USER adhp

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "info"]
