"""
Celery application configuration.
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "credit_network",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "check-cluster-health-nightly": {
        "task": "app.tasks.cluster_tasks.check_all_cluster_health",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
    },
    "send-repayment-reminders": {
        "task": "app.tasks.loan_tasks.send_upcoming_repayment_reminders",
        "schedule": crontab(hour=9, minute=0),  # 9 AM daily
    },
}

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
