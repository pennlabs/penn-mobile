from django.core.cache import cache
from django.utils import timezone


VIEW_CACHE_KEY = "clearable_dining_menu_view_cache"
VIEW_CACHE_TIMEOUT = 60 * 60 * 3  # 3 hours


def _get_key(date_param):
    return f"{VIEW_CACHE_KEY}_{date_param if date_param is not None else timezone.now().date()}"


def get_menu_view_cache(date_param):
    return cache.get(_get_key(date_param))


def set_menu_view_cache(date_param, data):
    cache.set(_get_key(date_param), data, timeout=VIEW_CACHE_TIMEOUT)


def delete_menu_view_cache(date_param):
    cache.delete(_get_key(date_param))
