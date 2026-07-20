from server.celery.celery_app import celery_app
from server.statistics.heatmap_calculator import HeatmapCalculator

_calculator = HeatmapCalculator()

@celery_app.task(
    name="server.tasks.statistics.recalcular_heatmap",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def recalcular_heatmap() -> None:
    _calculator.calcular()