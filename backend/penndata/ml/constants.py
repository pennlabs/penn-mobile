TIMEZONE = "America/New_York"

BUCKET_EDGES = [0.25, 0.50, 0.75]
BUCKET_NAMES = ["Not busy", "Moderate", "Busy", "Very busy"]

OPEN_TIMES = {
    0: (6, 23.5),
    1: (6, 23.5),
    2: (6, 23.5),
    3: (6, 23.5),
    4: (6, 22),
    5: (8, 22),
    6: (9, 22),
}

# Approximate Penn calendar (MMDD ranges) used when CalendarEvent is empty.
SESSION_MD = [(110, 505), (828, 1220)]
FINALS_MD = [(425, 505), (1208, 1220)]

BASE_FEATURES = ["room_id", "minute_of_day", "dow", "month", "is_weekend", "is_open"]
CAL_FEATURES = ["is_holiday", "in_session", "finals_window"]
LAGS_7D = ["lag_7d", "lag_wk_mean4"]
LAGS_24H = ["lag_1d"] + LAGS_7D
LAGS_1H = ["lag_1h"] + LAGS_24H

HORIZON_FEATURES = {
    "1h": BASE_FEATURES + LAGS_1H + CAL_FEATURES,
    "24h": BASE_FEATURES + LAGS_24H + CAL_FEATURES,
    "7d": BASE_FEATURES + LAGS_7D + CAL_FEATURES,
}

GBM_PARAMS = dict(max_depth=3, learning_rate=0.05, max_iter=300, random_state=0)
