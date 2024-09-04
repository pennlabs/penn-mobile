from enum import Enum

from analytics.analytics import AnalyticsTxn, LabsAnalytics, Product


try:
    AnalyticsEngine = LabsAnalytics()
except Exception as e:
    print("Error initializing AnalyticsEngine: ", e)
    AnalyticsEngine = None


class Metric(str, Enum):
    FITNESS = "fitness"


# TODO: Support multiple data objects in a single transaction
def record_analytics(metric, username=None, value="1"):
    if not AnalyticsEngine:
        print("AnalyticsEngine not initialized")
        return
    txn = AnalyticsTxn(Product.MOBILE_BACKEND, None, data=[{"key": metric, "value": value}])
    AnalyticsEngine.submit(txn)
