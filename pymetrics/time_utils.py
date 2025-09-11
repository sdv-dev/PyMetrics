"""Time utility functions."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype


def get_current_year(tz=None):
    """Get the current year."""
    return datetime.now(tz=tz).year


def get_current_utc():
    """Get the current datetime UTC."""
    return datetime.now(ZoneInfo('UTC'))


def get_first_datetime_in_year(year, tzinfo=None):
    """Get the first possible datetime value in a given year."""
    min_date = datetime(year, day=1, month=1).date()
    return datetime.combine(min_date, time=datetime.min.time(), tzinfo=tzinfo)


def get_last_datetime_in_year(year, tzinfo=None):
    """Get the last possible datetime value in a given year."""
    max_date = datetime(year, day=31, month=12).date()
    return datetime.combine(max_date, time=datetime.max.time(), tzinfo=tzinfo)


def get_min_max_dt_in_year(year):
    """Get the max/min datetime values in a given year."""
    min_datetime = get_first_datetime_in_year(year)
    max_datetime = get_last_datetime_in_year(year)
    return min_datetime, max_datetime


def drop_duplicates_by_date(df, time_column, group_by_columns):
    """Keep only the latest record for each day within each group.

    For each unique combination of date and group, retain only the row with the
    latest timestamp. This is useful for deduplicating time series data where
    multiple records may exist for the same day.

    Args:
        df (pd.DataFrame): Input DataFrame containing the data to deduplicate.
        time_column (str): Name of the column containing timestamp data.
        group_by_columns (list[str]): Name of the column to group by when determining duplicates.

    """
    df_copy = df.copy()
    date_column = _create_unique_name('date', df_copy.columns.tolist())
    original_dtype = None
    if not is_datetime64_any_dtype(df_copy[time_column].dtype):
        original_dtype = df_copy[time_column].dtype
        df_copy[time_column] = pd.to_datetime(df_copy[time_column], utc=True)
    df_copy[date_column] = df_copy[time_column].dt.date
    columns = [date_column] + group_by_columns
    df_copy = df_copy.loc[df_copy.groupby(columns)[time_column].idxmax()]
    df_copy = df_copy.drop(columns=date_column)
    if original_dtype:
        df_copy[time_column] = df[time_column].astype(original_dtype)
    return df_copy


def _create_unique_name(name, list_names):
    # Copied from https://github.com/sdv-dev/SDV/blob/dcc95725af4f249fc8e9015c6d2617184de95041/sdv/_utils.py#L184
    """Modify the ``name`` parameter if it already exists in the list of names."""
    result = name
    while result in list_names:
        result += '_'

    return result


def format_datetime_as_date(dt: datetime):
    """Format datetime as spelled out date (Month Day, Year)."""
    return dt.strftime('%B %-d, %Y')


def get_dt_now_spelled_out():
    """Get the current date as full spelled out string."""
    return format_datetime_as_date(datetime.now())
