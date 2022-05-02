from unittest import mock

from xmlrunner.extra.djangotestrunner import XMLTestRunner


def check_wharton(*args):
    return False


class MobileTestRunner(XMLTestRunner):
    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def run_tests(self, test_labels, **kwargs):
        return super().run_tests(test_labels, **kwargs)
