from datetime import datetime

import pandas as pd

from pymetrics.time_utils import (
    drop_duplicates_by_date,
    get_current_year,
    get_first_datetime_in_year,
    get_last_datetime_in_year,
    get_min_max_dt_in_year,
)


def test_current_year():
    # Run and Assert
    assert get_current_year() in list(range(2025, 2035))


def test_get_first_datetime_in_year():
    # Setup
    year = 2025

    # Run
    dt = get_first_datetime_in_year(year)

    # Assert
    assert dt == datetime(year, 1, 1, 0, 0, 0, 0, tzinfo=None)


def test_get_last_datetime_in_year():
    # Setup
    year = 2030

    # Run
    dt = get_last_datetime_in_year(year)

    # Assert
    assert dt == datetime(
        year=year, month=12, day=31, hour=23, minute=59, second=59, microsecond=999999, tzinfo=None
    )


def test_get_min_max_dt_in_year():
    # Setup
    year = 2021

    # Run
    min_dt, max_dt = get_min_max_dt_in_year(year)

    # Assert
    assert min_dt.year == year
    assert max_dt.year == year
    assert min_dt.month == 1
    assert max_dt.month == 12
    assert min_dt.microsecond == 0
    assert max_dt.microsecond == 999999


def test_drop_duplicates_by_date_basic():
    # Setup
    df = pd.DataFrame({
        'timestamp': ['2023-01-01 10:00:00', '2023-01-01 15:00:00', '2023-01-02 12:00:00'],
        'pkg_name': ['sdv', 'sdv', 'sdv'],
        'counts': [1, 2, 3],
    })

    # Run
    result = drop_duplicates_by_date(df, 'timestamp', ['pkg_name'])

    # Assert
    assert len(result) == 2
    assert result.iloc[0]['counts'] == 2
    assert result.iloc[1]['counts'] == 3


def test_drop_duplicates_by_date_multiple_groups():
    # Setup
    df = pd.DataFrame({
        'timestamp': [
            '2023-01-01 09:00:00',
            '2023-01-01 14:00:00',
            '2023-01-01 11:00:00',
            '2023-01-01 16:00:00',
        ],
        'pkg_name': ['sdv', 'sdv', 'mostlyai', 'mostlyai'],
        'counts': [1, 2, 3, 4],
    })

    # Run
    result = drop_duplicates_by_date(df, 'timestamp', ['pkg_name'])

    # Assert
    assert len(result) == 2
    sdv_row = result[result['pkg_name'] == 'sdv'].iloc[0]
    mostlyai_row = result[result['pkg_name'] == 'mostlyai'].iloc[0]
    assert sdv_row['counts'] == 2
    assert mostlyai_row['counts'] == 4


def test_drop_duplicates_by_date_no_duplicates():
    # Setup
    df = pd.DataFrame({
        'timestamp': ['2023-01-01 10:00:00', '2023-01-02 11:00:00', '2023-01-03 12:00:00'],
        'pkg_name': ['sdv', 'sdv', 'mostlyai'],
        'counts': [1, 2, 3],
    })

    # Run
    result = drop_duplicates_by_date(df, 'timestamp', ['pkg_name'])

    # Assert
    assert len(result) == 3
    pd.testing.assert_frame_equal(result.reset_index(drop=True), df.reset_index(drop=True))
