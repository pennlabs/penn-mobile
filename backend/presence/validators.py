import datetime
import math
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError


def validate_geofence(value):
    if value == {}:
        return
    if not isinstance(value, dict) or set(value) != {"lat", "lng", "radius_m"}:
        raise ValidationError("Geofence must contain lat, lng, and radius_m.")
    for field, minimum, maximum in (("lat", -90, 90), ("lng", -180, 180), ("radius_m", 1, None)):
        number = value[field]
        if (
            isinstance(number, bool)
            or not isinstance(number, (int, float))
            or not math.isfinite(number)
            or number < minimum
            or (maximum is not None and number > maximum)
        ):
            raise ValidationError(f"Invalid geofence {field}.")


def validate_opening_hours(value):
    """Validate local weekly hours and date overrides; an empty object means unknown."""
    if value == {}:
        return
    if not isinstance(value, dict) or set(value) != {"timezone", "weekly", "overrides"}:
        raise ValidationError("Hours must contain timezone, weekly, and overrides.")
    try:
        ZoneInfo(value["timezone"])
    except (ZoneInfoNotFoundError, TypeError, ValueError):
        raise ValidationError("Hours must use a valid IANA timezone.")
    weekly, overrides = value["weekly"], value["overrides"]
    if not isinstance(weekly, dict) or not isinstance(overrides, dict):
        raise ValidationError("Weekly hours and date overrides must be objects.")
    if not weekly and not overrides:
        raise ValidationError("Provide weekly hours or date overrides.")
    if set(weekly) - set("0123456"):
        raise ValidationError("Weekly keys must be 0 (Monday) through 6 (Sunday).")
    for day in overrides:
        try:
            if datetime.date.fromisoformat(day).isoformat() != day:
                raise ValueError
        except (TypeError, ValueError):
            raise ValidationError("Override keys must be dates formatted YYYY-MM-DD.")
    for intervals in [*weekly.values(), *overrides.values()]:
        if not isinstance(intervals, list):
            raise ValidationError("Each day must contain a list of open/close intervals.")
        previous_close = -1
        for interval in intervals:
            if not isinstance(interval, dict) or set(interval) != {"open", "close"}:
                raise ValidationError("Each interval must contain open and close.")
            minutes = []
            for field in ("open", "close"):
                time = interval[field]
                if field == "close" and time == "24:00":
                    minutes.append(24 * 60)
                elif isinstance(time, str) and re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", time):
                    hour, minute = map(int, time.split(":"))
                    minutes.append(hour * 60 + minute)
                else:
                    raise ValidationError("Times must use HH:MM; closing may use 24:00.")
            start, end = minutes
            if start >= end or start < previous_close:
                raise ValidationError(
                    "Intervals must be ordered, non-overlapping, and open < close."
                )
            previous_close = end
