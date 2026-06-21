from server.enrichment.base import BaseEnricher
from server.validator.validator import Validator

class SeverityEnricher(BaseEnricher):
    def enrich(self, reporte: dict) -> dict:
        reporte["severidad"] = Validator.get_severity(reporte["report_type"])
        return reporte