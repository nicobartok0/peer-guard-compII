import os
from celery import Celery
from dotenv import load_dotenv
from pathlib import Path
from kombu import Queue


# Cargar .env correctamente
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"

celery_app = Celery(
    "server",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
)

celery_app.conf.task_queues = (
    Queue("enriquecimiento"),
    Queue("persistencia"),
    Queue("estadistica")
)

celery_app.conf.task_routes = {
    "server.tasks.enrichment.enriquecer": {"queue": "enriquecimiento"},
    "server.tasks.persistence.persistir": {"queue": "persistencia"},
    "server.tasks.statistics.calcular_estadistica": {"queue": "estadistica"},
}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    timezone="UTC",
    enable_utc=True,

    task_track_started=True,
    task_time_limit=30,

    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    result_expires=3600,
)

celery_app.autodiscover_tasks(["server"])