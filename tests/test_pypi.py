from datetime import datetime
from unittest.mock import patch

import pytest

from download_analytics.pypi import _get_query_dates


@patch('download_analytics.pypi.datetime')
def test__get_query_dates_all_dates_none(datetime_mock):
    """If all dates are none, end is utcnow and start is end - max_days.

    Setup:
        - mock utcnow to 2021-11-30

    Input:
        - all Nones, max_days = 3

    Expected Output:
        - start_date = 2021-11-27
        - end_date = 2021-11-30
    """
    # setup
    datetime_mock.utcnow.return_value = datetime(2021, 11, 30)

    # run
    start_date, end_date = _get_query_dates(
        start_date=None,
        min_date=None,
        max_date=None,
        max_days=3,
    )

    # assert
    assert start_date == datetime(2021, 11, 27)
    assert end_date == datetime(2021, 11, 30)


@patch('download_analytics.pypi.datetime')
def test__get_query_dates_start_date_given_min_max_none(datetime_mock):
    """If only start_date is given and min/max are None, return start_date and utcnow.

    Setup:
        - mock utcnow to 2021-11-30

    Input:
        - start_date given
        - min and max dates None
        - max days = 3

    Expected Output:
        - start_date = given start date
        - end_date = utcnow
    """
    # setup
    datetime_mock.utcnow.return_value = datetime(2021, 11, 30)

    # run
    start_date, end_date = _get_query_dates(
        start_date=datetime(2021, 11, 1),
        min_date=None,
        max_date=None,
        max_days=3,
    )

    # assert
    assert start_date == datetime(2021, 11, 1)
    assert end_date == datetime(2021, 11, 30)


def test__get_query_dates_start_date_given_min_after_start():
    """If start_date is given and min_date is after, return start_date and min_date.

    Input:
        - start_date given
        - min_date after start_date
        - max_date after min_date
        - max days = 3

    Expected Output:
        - start_date = given start date
        - end_date = min_date
    """
    # run
    start_date, end_date = _get_query_dates(
        start_date=datetime(2021, 11, 1),
        min_date=datetime(2021, 11, 5),
        max_date=datetime(2021, 11, 15),
        max_days=3,
    )

    # assert
    assert start_date == datetime(2021, 11, 1)
    assert end_date == datetime(2021, 11, 5)


@patch('download_analytics.pypi.datetime')
def test__get_query_dates_start_date_given_min_after_start_force_true(datetime_mock):
    """If start_date is given and force is true, return start_date utcnow always.

    Setup:
        - mock utcnow to 2021-11-30

    Input:
        - start_date given
        - min_date after start_date
        - max_date after min_date
        - max days = 3
        - force = True

    Expected Output:
        - start_date = given start date
        - end_date = utcnow
    """
    # setup
    datetime_mock.utcnow.return_value = datetime(2021, 11, 30)

    # run
    start_date, end_date = _get_query_dates(
        start_date=datetime(2021, 11, 1),
        min_date=datetime(2021, 11, 5),
        max_date=datetime(2021, 11, 15),
        max_days=3,
        force=True,
    )

    # assert
    assert start_date == datetime(2021, 11, 1)
    assert end_date == datetime(2021, 11, 30)


@patch('download_analytics.pypi.datetime')
def test__get_query_dates_start_date_given_max_after(datetime_mock):
    """If start_date is given, min_date before and max_date is after, return max_date and utcnow.

    Setup:
        - mock utcnow to 2021-11-30

    Input:
        - start_date given
        - min_date before start_date
        - max_date after start_date
        - max days = 3

    Expected Output:
        - start_date = max_date
        - end_date = utcnow
    """
    # setup
    datetime_mock.utcnow.return_value = datetime(2021, 11, 30)

    # run
    start_date, end_date = _get_query_dates(
        start_date=datetime(2021, 11, 10),
        min_date=datetime(2021, 11, 1),
        max_date=datetime(2021, 11, 15),
        max_days=3,
    )

    # assert
    assert start_date == datetime(2021, 11, 15)
    assert end_date == datetime(2021, 11, 30)


@patch('download_analytics.pypi.datetime')
def test__get_query_dates_start_date_given_max_after_force_true(datetime_mock):
    """If start_date is given and force is true, return start_date and utcnow always.

    Setup:
        - mock utcnow to 2021-11-30

    Input:
        - start_date given
        - min_date before start_date
        - max_date after start_date
        - max days = 3
        - force = True

    Expected Output:
        - start_date = start_date
        - end_date = utcnow
    """
    # setup
    datetime_mock.utcnow.return_value = datetime(2021, 11, 30)

    # run
    start_date, end_date = _get_query_dates(
        start_date=datetime(2021, 11, 10),
        min_date=datetime(2021, 11, 1),
        max_date=datetime(2021, 11, 15),
        max_days=3,
        force=True,
    )

    # assert
    assert start_date == datetime(2021, 11, 10)
    assert end_date == datetime(2021, 11, 30)


def test__get_query_dates_start_date_given_max_before():
    """If start_date is given, max is before and force is false, raise an error.

    Input:
        - start_date given
        - min_date before start_date
        - max_date before start_date
        - max days = 3

    Expected Output:
        - start_date = start_date
        - end_date = utcnow
    """
    # run
    msg = 'start_date=2021-11-15 00:00:00 and max_date=2021-11-10 00:00:00 are creating a gap'
    with pytest.raises(ValueError, match=msg):
        start_date, end_date = _get_query_dates(
            start_date=datetime(2021, 11, 15),
            min_date=datetime(2021, 11, 1),
            max_date=datetime(2021, 11, 10),
            max_days=3,
        )


@patch('download_analytics.pypi.datetime')
def test__get_query_dates_start_date_given_max_before_force_true(datetime_mock):
    """If start_date is given, max is before and force is true, return start_date, utcnow.

    Setup:
        - mock utcnow to 2021-11-30

    Input:
        - start_date given
        - min_date before start_date
        - max_date before start_date
        - max days = 3
        - force = True

    Expected Output:
        - start_date = start_date
        - end_date = utcnow
    """
    # setup
    datetime_mock.utcnow.return_value = datetime(2021, 11, 30)

    # run
    start_date, end_date = _get_query_dates(
        start_date=datetime(2021, 11, 15),
        min_date=datetime(2021, 11, 1),
        max_date=datetime(2021, 11, 10),
        max_days=3,
        force=True,
    )

    # assert
    assert start_date == datetime(2021, 11, 15)
    assert end_date == datetime(2021, 11, 30)
