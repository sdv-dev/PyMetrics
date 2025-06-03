"""Functions to get PyPI downloads from Google Big Query."""

import logging
from datetime import datetime, timedelta, timezone

import pandas as pd

from download_analytics.bq import run_query

LOGGER = logging.getLogger(__name__)


QUERY_TEMPLATE = """
SELECT
    timestamp,
    country_code,
    file.project                    as project,
    file.version                    as version,
    file.type                       as type,
    details.installer.name          as installer_name,
    details.implementation.name     as implementation_name,
    details.implementation.version  as implementation_version,
    details.distro.name             as distro_name,
    details.distro.version          as distro_version,
    details.system.name             as system_name,
    details.system.release          as system_release,
    details.cpu                     as cpu,
FROM `bigquery-public-data.pypi.file_downloads`
WHERE file.project in {projects}
    AND timestamp > '{start_date}'
    AND timestamp < '{end_date}'
"""
OUTPUT_COLUMNS = [
    'timestamp',
    'country_code',
    'project',
    'version',
    'type',
    'installer_name',
    'implementation_name',
    'implementation_version',
    'distro_name',
    'distro_version',
    'system_name',
    'system_release',
    'cpu',
]


def _get_query(projects, start_date, end_date):
    if isinstance(projects, list):
        projects = tuple(projects)

    if not isinstance(projects, str) and len(projects) == 1:
        projects = projects[0]

    if isinstance(projects, str):
        projects = f"('{projects}')"

    LOGGER.info('Querying for projects `%s` between `%s` and `%s`', projects, start_date, end_date)

    return QUERY_TEMPLATE.format(
        projects=projects,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )


def _get_query_dates(start_date, min_date, max_date, max_days, force=False):
    end_date = datetime.now(timezone.utc).date()
    if start_date is None:
        start_date = end_date - timedelta(days=max_days)

    start_date = start_date.date()

    if pd.notna(min_date):
        min_date = pd.Timestamp(min_date).date()
        if min_date > start_date:
            if not force:
                end_date = min_date

    elif pd.notna(max_date) and not force:
        max_date = pd.Timestamp(max_date).date()
        if max_date > start_date:
            start_date = max_date
        else:
            raise ValueError(f'start_date={start_date} and max_date={max_date} are creating a gap')

    return start_date, end_date


def get_pypi_downloads(
    projects,
    start_date=None,
    end_date=None,
    previous=None,
    max_days=1,
    credentials_file=None,
    dry_run=False,
    force=False,
):
    """Get PyPI downloads data from the Big Query dataset.

    Args:
        projects (list[str]):
            List of projects to grab data for.
        start_date (Union[datetime, NoneType]):
            Date from which to start collecting data. If `None`,
            start_date will be `end_date - max_days`.
        end_date (Union[datetime, NoneType]):
            Date up to which to collecting data. If `None`,
            it will be the current date.
        previous (Union[pandas.DataFrame, NoneType]):
            pandas.DataFrame with previously obtained downloads data.
        max_days (int):
            Maximum amount of days to include in the query from current date back, in case
            `start_date` has not been provided. Defaults to 1.
        credentials_file (str):
            Path to the GCP Credentials file for BigQuery.
        dry_run (bool):
            If `True`, do not run the actual query. Defaults to `False`.
        force (bool):
            Whether to force the query even if data already exists or the dates
            combination creates a gap. Defaults to False.

    Returns:
        pandas.DataFrame:
            Table with all the collected downloads, including any of the lines
            listed in the ``previous`` table.
    """
    if previous is not None:
        if isinstance(projects, str):
            projects = (projects,)

        previous_projects = previous[previous.project.isin(projects)]
        min_date = previous_projects.timestamp.min().date()
        max_date = previous_projects.timestamp.max().date()
    else:
        previous = pd.DataFrame(columns=OUTPUT_COLUMNS)
        min_date = None
        max_date = None

    start_date, end_date = _get_query_dates(start_date, min_date, max_date, max_days, force)
    query = _get_query(projects, start_date, end_date)

    new_downloads = run_query(query, dry_run, credentials_file)
    if new_downloads is None or new_downloads.empty:
        all_downloads = previous
    else:
        new_downloads['timestamp'] = new_downloads['timestamp'].dt.tz_convert(None)
        new_downloads = new_downloads.sort_values('timestamp')
        if max_date is None:
            all_downloads = new_downloads
        else:
            if max_date <= end_date:
                before = previous[previous.timestamp < new_downloads.timestamp.min()]
                after = new_downloads
            else:
                before = new_downloads
                after = previous[previous.timestamp > new_downloads.timestamp.max()]

            all_downloads = pd.concat([before, after], ignore_index=True)

    LOGGER.info('Obtained %s new downloads', len(all_downloads) - len(previous))
    return all_downloads
