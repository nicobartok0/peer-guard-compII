from server.factory.factory import Factory
from server.domain.report import Report

class ReportFactory(Factory):
    @staticmethod
    def create(message_json):
        return Report(**message_json)
    