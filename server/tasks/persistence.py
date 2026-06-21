from server.celery.celery_app import celery_app

@celery_app.task(name="server.tasks.persistence.persistir")
def persistir(reporte: dict):
    # acá va el INSERT a MariaDB
    print("Persistiendo reporte:", reporte)
    ...