from enum import IntEnum

class Cache(IntEnum):
    MINUTE = 60
    HOUR = MINUTE * 60
    DAY = HOUR * 24
    MONTH = 30 * DAY
    YEAR = 365 * DAY