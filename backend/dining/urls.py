from django.urls import path

from dining.views import (
    AverageBalance,
    Balance,
    DailyMenu,
    DiningItem,
    Hours,
    Menus,
    Preferences,
    Projection,
    Transactions,
    Venues,
    WeeklyMenu,
)


urlpatterns = [
    path("venues/", Venues.as_view(), name="venues"),
    path("menus/", Menus.as_view(), name="Menus"),
    path("hours/<venue_id>/", Hours.as_view(), name="hours"),
    path("weekly_menu/<venue_id>/", WeeklyMenu.as_view(), name="weekly-menu"),
    path("daily_menu/<venue_id>/", DailyMenu.as_view(), name="daily-menu"),
    path("item/<item_id>/", DiningItem.as_view(), name="item-info"),
    path("preferences/", Preferences.as_view(), name="dining-preferences"),
    path("transactions/", Transactions.as_view(), name="dining-transactions"),
    path("balance/", Balance.as_view(), name="dining-balance"),
    path("balances", AverageBalance.as_view(), name="dining-balance-average"),
    path("projection/", Projection.as_view(), name="dining-projection"),
]
