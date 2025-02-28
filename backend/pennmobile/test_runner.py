from unittest import mock

from django.test.runner import DiscoverRunner
from xmlrunner.extra.djangotestrunner import XMLTestRunner


def check_wharton(*args):
    return False


class MockLabsAnalytics:

    def __init__(self):
        pass

    def submit(self, txn):
        pass


class MobileTestCIRunner(XMLTestRunner):
    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def run_tests(self, test_labels, **kwargs):
        return super().run_tests(test_labels, **kwargs)


class MobileTestLocalRunner(DiscoverRunner):
    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def run_tests(self, test_labels, **kwargs):
        return super().run_tests(test_labels, **kwargs)
