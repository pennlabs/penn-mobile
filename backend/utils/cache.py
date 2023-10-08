from enum import IntEnum


class Cache(IntEnum):
    MINUTE = 60
    HOUR = 60 * MINUTE
    DAY = 24 * HOUR
    MONTH = 30 * DAY
    YEAR = 365 * DAY
