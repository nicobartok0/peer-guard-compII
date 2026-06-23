from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Report(Base):
    __tablename__ = "reports"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    report_type     = Column(String(50),  nullable=False)
    datetime        = Column(String(19),  nullable=False)  # "YYYY-MM-DD HH:MM:SS"
    lat             = Column(Float,       nullable=False)
    long            = Column(Float,       nullable=False)
    detail          = Column(Text,        nullable=True)
    dia_semana      = Column(Integer,     nullable=False)
    hora            = Column(Integer,     nullable=False)
    franja_horaria  = Column(String(20),  nullable=False)
    severidad       = Column(Integer,     nullable=False)
    barrio          = Column(String(100), nullable=True)
    ciudad          = Column(String(100), nullable=True)
    provincia       = Column(String(100), nullable=True)
    temperatura     = Column(Float,       nullable=True)
    precipitacion   = Column(Float,       nullable=True)

    def __repr__(self):
        return f"<Report {self.id} | {self.report_type} | {self.datetime}>"