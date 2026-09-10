FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY dags ./dags

# Exécution sans privilèges (C4.4.1 — test de sécurité).
RUN useradd --create-home --uid 1000 eckert
USER eckert

CMD ["python", "-c", "import eckert; print('image eckert operationnelle')"]
