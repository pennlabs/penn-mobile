from unittest import mock

from django.test.runner import DiscoverRunner


def check_wharton(*args):
    return False


class MobileTestRunner(DiscoverRunner):
    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def run_tests(self, test_labels, **kwargs):
        print('i also went here')
        return super().run_tests(test_labels, **kwargs)
