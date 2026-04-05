"""Risk subsystem constants."""

STYLE_VERSION = "barra_cn_simplified_v1"

STYLE_NAMES = [
    "log_circ_cap",
    "book_to_price",
    "mom_12_1",
    "str_1m",
    "vol_20d",
    "turnover_20d",
    "ep_ratio",
]

REQUIRED_FIELDS = [
    "$close",
    "$circ_market_cap",
    "$pb_ratio",
    "$pe_ratio",
    "$turnover_rate",
]

LOOKBACK_CALENDAR_DAYS = 400  # ~260 trading days, covers 252 for momentum

CACHE_SUBDIR = "risk"

# Crowding thresholds
CROWDING_R2_HIGH = 0.25
CROWDING_R2_MEDIUM = 0.10
CROWDING_EXPOSURE_HIGH = 0.5
CROWDING_EXPOSURE_MEDIUM = 0.3

# Survival ratio
SURVIVAL_RAW_IC_MIN = 1e-4  # below this, survival = NaN
