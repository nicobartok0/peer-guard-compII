from server.repository.base import BaseRepository
from server.repository.models import Report
from server.repository.db import SessionLocal

class ReportRepository(BaseRepository):

    def save(self, reporte: dict) -> None:
        db = SessionLocal()
        try:
            report = Report(
                report_type    = reporte["report_type"],
                datetime       = reporte["datetime"],
                lat            = reporte["lat"],
                long           = reporte["long"],
                detail         = reporte.get("detail"),
                dia_semana     = reporte["dia_semana"],
                hora           = reporte["hora"],
                franja_horaria = reporte["franja_horaria"],
                severidad      = reporte["severidad"],
                barrio         = reporte.get("barrio"),
                ciudad         = reporte.get("ciudad"),
                provincia      = reporte.get("provincia"),
                temperatura    = reporte.get("temperatura"),
                precipitacion  = reporte.get("precipitacion"),
            )
            db.add(report)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()