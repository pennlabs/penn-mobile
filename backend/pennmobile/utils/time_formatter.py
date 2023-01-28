import datetime

from django.utils.timezone import make_aware


EXPECTED_DATETIME_FORMAT = "%Y-%m-%d"
EXPECTED_DATETIME_FORMAT_LONG = "%Y-%m-%dT%H:%M:%S%z"


def parse_time(date_param) -> datetime:
    return make_aware(datetime.datetime.strptime(date_param, EXPECTED_DATETIME_FORMAT))


def parse_time_long(date_param) -> datetime:
    return datetime.datetime.strptime(date_param, EXPECTED_DATETIME_FORMAT_LONG)


def stringify_date(date) -> str:
    return date.strftime(EXPECTED_DATETIME_FORMAT)
