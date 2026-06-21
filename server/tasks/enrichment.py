from server.celery.celery_app import celery_app
from server.enrichment.pipeline import EnrichmentPipeline
from server.enrichment.time_enricher import TimeEnricher
from server.enrichment.severity_enricher import SeverityEnricher
from server.enrichment.geo_enricher import GeoEnricher
from server.enrichment.weather_enricher import WeatherEnricher
from server.tasks.persistence import persistir

pipeline = EnrichmentPipeline([
    TimeEnricher(),
    SeverityEnricher(),
    GeoEnricher(),
    WeatherEnricher(),
])

@celery_app.task(name="server.tasks.enrichment.enriquecer")
def enriquecer(reporte: dict):
    reporte = pipeline.run(reporte)
    persistir.delay(reporte)