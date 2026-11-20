FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Caso uses collectstatic e tenhas STATIC_ROOT configurado no settings.py:
# RUN python manage.py collectstatic --noinput

EXPOSE 8080

# Substitui "agenda.wsgi:application" caso o teu ficheiro wsgi.py esteja noutro pacote
CMD ["gunicorn", "agenda.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "2"]
