import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schedularos.settings')

app = Celery('schedularos')

# Load Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'scan-due-steps': {
        'task': 'orchestration.tasks.scan_due_steps',
        'schedule': 30.0,  # every 30 seconds
    },
    'expire-proposals': {
        'task': 'proposals.tasks.expire_stale_proposals',
        'schedule': 300.0,  # every 5 minutes
    },
    'reset-daily-budgets': {
        'task': 'core.tasks.reset_daily_budgets',
        'schedule': crontab(hour=0, minute=0),  # midnight UTC
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
