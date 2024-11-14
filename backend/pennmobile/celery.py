import os
from typing import Any

from celery import Celery


# Checkout https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pennmobile.settings.development")

app = Celery("pennmobile")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self: Any) -> None:
    print(f"Request: {self.request!r}")
