class EnrichmentPipeline:
    def __init__(self, enrichers: list):
        self.enrichers = enrichers

    def run(self, reporte: dict) -> dict:
        for enricher in self.enrichers:
            reporte = enricher.enrich(reporte)
        return reporte