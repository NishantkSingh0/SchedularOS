.PHONY: api worker beat web test lint help

help:
	@echo "Available commands:"
	@echo "  make api      - Run Django API server"
	@echo "  make worker   - Run Celery worker"
	@echo "  make beat     - Run Celery beat scheduler"
	@echo "  make web      - Run React frontend dev server"
	@echo "  make migrate  - Run Django migrations"
	@echo "  make test     - Run tests"
	@echo "  make lint     - Run linting"

api:
	cd apps/api && source venv/bin/activate && python manage.py runserver 0.0.0.0:8000

worker:
	cd apps/api && source venv/bin/activate && celery -A schedularos worker -Q realtime,default,bulk,executor --loglevel=info

beat:
	cd apps/api && source venv/bin/activate && celery -A schedularos beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

web:
	cd apps/web && npm run dev

migrate:
	cd apps/api && python manage.py makemigrations
	cd apps/api && python manage.py migrate

test:
	cd apps/api && python manage.py test

lint:
	cd apps/api && flake8 .
	cd apps/api && mypy .
