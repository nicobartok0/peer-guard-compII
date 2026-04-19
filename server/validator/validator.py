import re
from datetime import datetime

class Validator:

# ESTRUCTURA A VALIDAR:
# message_json = {
#   report_type = (ROBO/HURTO, ROBO VEHÍCULO, ASESINATO, SINIESTRO VIAL),
#   datetime = (fecha en formato YYYY-MM-DD HH:MM:SS. El
#   factory lo convertirá en día y hora).
#   lat = (Latitud en GRADOS DECIMALES: (de -90 a 90))
#   long = (Longitud en GRADOS DECIMALES: (de -180 a 180))
#   detail = (Descripción entre 0 y 300 carácteres.)
#   
#}

    VALID_INPUT_STRUCTURE = {
        "report_type" : "",
        "datetime" : "",
        "lat" : 0.0,
        "long" : 0.0,
        "detail" : ""
    }
    VALID_TYPES = [
        "ROBO/HURTO",
        "ROBO VEHÍCULO",
        "ASESINATO",
        "SINIESTRO VIAL"
    ]
    DATE_FORMAT = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"

    @staticmethod
    def validate(message_json):
        # Validar la estructura del mensaje en JSON
        for key in message_json.keys():
            if key not in Validator.VALID_INPUT_STRUCTURE.keys():
                return False, "Estructura no válida"
            
        if message_json["report_type"] not in Validator.VALID_TYPES:
            return False, "Tipo no válido"
        
        if not re.match(Validator.DATE_FORMAT,message_json['datetime']):
            
            return False, "Formato de fecha no válido. Debe ser YYYY-MM-DD HH:MM:SS"
        
        try:
            message_json['datetime'] = datetime.strptime(message_json["datetime"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False, "Fecha con valores no válidos."
        
        if not (message_json["lat"] > -90) or not (message_json["lat"] < 90):
            return False, "Rango de latitud inválido"  
        
        if not (message_json["long"] > -180) or not (message_json["lat"] < 180):
            return False, "Rango de longitud inválido"  
        
        if not (len(message_json["detail"]) < 300):
            return False, "Detalle muy largo."
        
        return True, message_json
        
        
        


        