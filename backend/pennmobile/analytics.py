from enum import Enum

from analytics.analytics import AnalyticsTxn, LabsAnalytics, Product


AnalyticsEngine = LabsAnalytics()


class Metric(str, Enum):
    GSR_BOOK = "gsr.book"

    SUBLET_BROWSE = "sublet.browsed"
    SUBLET_FAVORITED = "sublet.favorited"
    SUBLET_OFFER = "sublet.offer"
    SUBLET_CREATED = "sublet.created"

    LAUNDRY_VIEWED = "laundry.viewed"

    PORTAL_POLL_VOTED = "portal.poll.voted"


def record_analytics(metric: Metric, username=None):
    txn = AnalyticsTxn(Product.MOBILE_BACKEND, username, data=[{"key": metric, "value": "1"}])
    AnalyticsEngine.submit(txn)
