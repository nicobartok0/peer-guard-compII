from server.celery.celery_app import celery_app
from server.repository.db import init_db
from server.repository.report_repository import ReportRepository

# Inicializar la DB al arrancar el worker, no en cada task
init_db()

_repository = ReportRepository()

@celery_app.task(
    name="server.tasks.persistence.persistir",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def persistir(reporte: dict) -> None:
    _repository.save(reporte)