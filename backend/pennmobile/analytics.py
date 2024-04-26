from enum import Enum

from analytics.analytics import AnalyticsTxn, LabsAnalytics, Product


AnalyticsEngine = LabsAnalytics()


class Metric(str, Enum):
    GSR_BOOK = "gsr.book"


def record_analytics(metric: Metric, username=None):
    txn = AnalyticsTxn(Product.MOBILE_BACKEND, username, data=[{"key": metric, "value": "1"}])
    AnalyticsEngine.submit(txn)
