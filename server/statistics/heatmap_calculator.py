import os
import json
from pathlib import Path
from dotenv import load_dotenv
import redis
from sqlalchemy import text
from server.repository.db import engine

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

_redis = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=2,
    decode_responses=True,  
)

FRANJAS = ("mañana", "tarde", "noche", "madrugada")
ZONA_SIN_BARRIO = "Sin barrio"


class HeatmapCalculator:

    def calcular(self) -> None:
        
        agregados = self._agregar_desde_db()
        self._escribir_en_redis(agregados)

    def _agregar_desde_db(self) -> dict:
        
        query = text("""
            SELECT
                COALESCE(barrio, :sin_barrio)  AS zona,
                franja_horaria,
                SUM(severidad)                 AS suma_severidad,
                COUNT(*)                       AS total
            FROM reports
            GROUP BY zona, franja_horaria
        """)

        agregados = {}

        with engine.connect() as conn:
            filas = conn.execute(query, {"sin_barrio": ZONA_SIN_BARRIO}).fetchall()

        for fila in filas:
            zona = fila.zona
            franja = fila.franja_horaria

            if zona not in agregados:
                agregados[zona] = {}

            agregados[zona][franja] = {
                "suma_severidad": float(fila.suma_severidad),
                "total":          int(fila.total),
            }

        return agregados

    def _escribir_en_redis(self, agregados: dict) -> None:
        pipe = _redis.pipeline()
        heatmap_completo = {}

        for zona, franjas in agregados.items():
            key = f"heatmap:barrio:{zona}"
            datos = {}
            total_zona = 0

            for franja in FRANJAS:
                if franja in franjas:
                    d = franjas[franja]
                    intensidad = round(d["suma_severidad"] / d["total"], 2)
                    datos[franja] = intensidad
                    total_zona += d["total"]
                else:
                    datos[franja] = 0.0

            datos["total"] = total_zona
            pipe.delete(key)
            pipe.hset(key, mapping={k: json.dumps(v) for k, v in datos.items()})

            # Acumulamos para el mensaje Pub/Sub
            heatmap_completo[zona] = datos

        pipe.execute()

        # Publicamos el heatmap completo en el canal para que
        # el conn_manager lo broadcastee a los clientes conectados.
        _redis.publish("heatmap_update", json.dumps(heatmap_completo))