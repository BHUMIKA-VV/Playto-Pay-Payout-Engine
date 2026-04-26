FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_merchants && python -m huey_consumer backend.huey_conf.huey & gunicorn backend.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
