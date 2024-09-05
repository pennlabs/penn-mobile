from enum import Enum

from analytics.analytics import AnalyticsTxn, LabsAnalytics, Product


try:
    AnalyticsEngine = LabsAnalytics()
except Exception as e:
    print("Error initializing AnalyticsEngine: ", e)
    AnalyticsEngine = None


class Metric(str, Enum):
    GSR_BOOK = "gsr.book"

    SUBLET_BROWSE = "sublet.browsed"
    SUBLET_FAVORITED = "sublet.favorited"
    SUBLET_OFFER = "sublet.offer"
    SUBLET_CREATED = "sublet.created"

    LAUNDRY_VIEWED = "laundry.viewed"

    PORTAL_POLL_VOTED = "portal.poll.voted"


# TODO: Support multiple data objects in a single transaction
def record_analytics(metric: str, username=None, value="1"):
    if not AnalyticsEngine:
        print("AnalyticsEngine not initialized")
        return
    txn = AnalyticsTxn(Product.MOBILE_BACKEND, username, data=[{"key": metric, "value": value}])
    AnalyticsEngine.submit(txn)
