from datetime import datetime
# Por ahora "Report" será un DTO. Se verá cómo evoluciona luego.

class Report:
    
    def __init__(self, report_type:str, datetime:datetime, lat:float, long:float, detail:str):
        self.report_type = report_type,
        self.datetime = datetime,
        self.lat = lat,
        self.long = long,
        self.detail = detail