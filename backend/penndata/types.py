from typing import Any, TypeAlias

from django.db.models import Manager, QuerySet

from penndata.models import CalendarEvent, Event, HomePageOrder


ValidatedData: TypeAlias = dict[str, Any]
CalendarEventList: TypeAlias = QuerySet[CalendarEvent, Manager[CalendarEvent]]
EventList: TypeAlias = QuerySet[Event, Manager[Event]]
HomePageOrderList: TypeAlias = QuerySet[HomePageOrder, Manager[HomePageOrder]]
