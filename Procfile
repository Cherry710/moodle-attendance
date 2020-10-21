web: gunicorn --bind 0.0.0.0:$PORT app:app
worker: celery worker -A app.celery --loglevel=info