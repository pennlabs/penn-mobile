from django.urls import path

from dining.views import DailyMenu, Dashboard, DiningItem, Hours, Venues, WeeklyMenu


app_name = "main"

urlpatterns = [
    path(r"", Dashboard.as_view()),
    path("venues/", Venues.as_view(), name="venues"),
    path("hours/<venue_id>/", Hours.as_view(), name="hours"),
    path("weekly_menu/<venue_id>/", WeeklyMenu.as_view(), name="weekly-menu"),
    path("daily_menu/<venue_id>/", DailyMenu.as_view(), name="daily-menu"),
    path("item/<item_id>/", DiningItem.as_view(), name="item-info"),
]
