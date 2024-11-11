from typing import Tuple

from django.db.models import Manager, QuerySet

from user.models import NotificationToken, NotificationSetting


TokenPair = Tuple[str, str]  # (username, token)
NotificationResult = Tuple[list[str], list[str]]  # (success_users, failed_users)

NotificationTokenQuerySet = QuerySet[NotificationToken, Manager[NotificationToken]]
NotificationSettingQuerySet = QuerySet[NotificationSetting, Manager[NotificationSetting]]
