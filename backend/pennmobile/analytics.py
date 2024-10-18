from enum import Enum
from functools import wraps
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


def record_analytics(metric: Metric, value: str = "1"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not AnalyticsEngine:
                print("AnalyticsEngine not initialized")
                return func(*args, **kwargs)

            # Call the original function
            result = func(*args, **kwargs)

            # Record the analytics
            username = kwargs.get("username", None)
            txn = AnalyticsTxn(
                Product.MOBILE_BACKEND, username, data=[{"key": metric, "value": value}]
            )
            AnalyticsEngine.submit(txn)

            return result

        return wrapper

    return decorator
