from server.celery.celery_app import celery_app
from server.validator.validator import Validator
from datetime import datetime

@celery_app.task(name="server.tasks.enrichment.enriquecer")
def enriquecer(reporte: dict):
    # Lógica de día y hora
    fecha = datetime.strptime(reporte['datetime'], '%Y-%m-%d %H:%M:%S')
    reporte['dia_semana'] = fecha.weekday()
    
    # lógica de enriquecimiento (día/hora a partir del datetime, severity score, etc.)
    reporte['severidad'] = Validator.get_severity(reporte['report_type'])
    
    from server.tasks.persistence import persistir
    persistir.delay(reporte)