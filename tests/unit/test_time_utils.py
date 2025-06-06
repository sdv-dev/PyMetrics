from datetime import datetime

from download_analytics.time_utils import (
    get_current_year,
    get_first_datetime_in_year,
    get_min_max_dt_in_year,
    get_last_datetime_in_year,
)

def test_current_year():
    assert get_current_year() in list(range(2025, 2035))

def test_get_first_datetime_in_year():
    year = 2025
    dt = get_first_datetime_in_year(year)
    assert dt == datetime(year, 1, 1, 0, 0, 0, 0, tzinfo=None)


def test_get_last_datetime_in_year():
    year = 2030
    dt = get_last_datetime_in_year(year)
    assert dt == datetime(year=year, month=12, day=31, hour=23, minute=59, second=59,
                          microsecond=999999, tzinfo=None)


def test_get_min_max_dt_in_year():
    year = 2021
    min_dt, max_dt = get_min_max_dt_in_year(year)
    assert min_dt.year == year
    assert max_dt.year == year
    assert min_dt.month == 1
    assert max_dt.month == 12
    assert min_dt.microsecond == 0
    assert max_dt.microsecond == 999999