"""
Celery background tasks.
"""
from app.tasks.celery_app import celery_app
from app.tasks.scoring_tasks import compute_trust_score_task
from app.tasks.cluster_tasks import check_cluster_health_task, check_all_cluster_health
from app.tasks.loan_tasks import send_repayment_reminder_task, send_upcoming_repayment_reminders

__all__ = [
    "celery_app",
    "compute_trust_score_task",
    "check_cluster_health_task",
    "check_all_cluster_health",
    "send_repayment_reminder_task",
    "send_upcoming_repayment_reminders",
]
