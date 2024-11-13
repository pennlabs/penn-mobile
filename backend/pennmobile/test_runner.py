from typing import Any
from unittest import mock

from django.test.runner import DiscoverRunner
from xmlrunner.extra.djangotestrunner import XMLTestRunner


def check_wharton(*args: Any) -> bool:
    return False


class MockLabsAnalytics:

    def __init__(self) -> None:
        pass

    def submit(self, txn: Any) -> None:
        pass


class MobileTestCIRunner(XMLTestRunner):
    @mock.patch("analytics.analytics.LabsAnalytics", MockLabsAnalytics)
    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def run_tests(self, test_labels: list[str], **kwargs: Any) -> int:
        return super().run_tests(test_labels, **kwargs)


class MobileTestLocalRunner(DiscoverRunner):
    @mock.patch("analytics.analytics.LabsAnalytics", MockLabsAnalytics)
    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def run_tests(self, test_labels: list[str], **kwargs: Any) -> int:
        return super().run_tests(test_labels, **kwargs)
