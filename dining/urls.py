from django.urls import path

<<<<<<< HEAD
from dining.views import (
    AverageBalance,
    Balance,
    DailyMenu,
    Dashboard,
    DiningItem,
    Hours,
    Preferences,
    Projection,
    Transactions,
    Venues,
    WeeklyMenu,
)
=======
from dining.views import DailyMenu, Dashboard, DiningItem, Hours, Venues, WeeklyMenu
>>>>>>> d3f6306d09f285f0293e8c0148e17a34e80ff3d1


app_name = "main"

urlpatterns = [
    path(r"", Dashboard.as_view()),
    path("venues/", Venues.as_view(), name="venues"),
    path("hours/<venue_id>/", Hours.as_view(), name="hours"),
    path("weekly_menu/<venue_id>/", WeeklyMenu.as_view(), name="weekly-menu"),
    path("daily_menu/<venue_id>/", DailyMenu.as_view(), name="daily-menu"),
    path("item/<item_id>/", DiningItem.as_view(), name="item-info"),
<<<<<<< HEAD
    path("preferences/", Preferences.as_view(), name="dining-preferences"),
    path("transactions/", Transactions.as_view(), name="dining-transactions"),
    path("balance/", Balance.as_view(), name="dining-balance"),
    path("balances/", AverageBalance.as_view(), name="dining-balance-average"),
    path("projection/", Projection.as_view(), name="dining-projection"),
=======
>>>>>>> d3f6306d09f285f0293e8c0148e17a34e80ff3d1
]
