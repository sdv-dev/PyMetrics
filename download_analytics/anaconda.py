"""Functions to get Anaconda downloads from Anaconda S3 bucket."""

import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import requests
from tqdm import tqdm

from download_analytics.output import append_row, create_csv, get_path, load_csv
from download_analytics.time_utils import drop_duplicates_by_date

LOGGER = logging.getLogger(__name__)
dir_path = os.path.dirname(os.path.realpath(__file__))


BUCKET_NAME = 'anaconda-package-data'
PREVIOUS_ANACONDA_FILENAME = 'anaconda.csv'
PREVIOUS_ANACONDA_ORG_OVERALL_FILENAME = 'anaconda_org_overall.csv'
PREVIOUS_ANACONDA_ORG_VERSION_FILENAME = 'anaconda_org_per_version.csv'
TIME_COLUMN = 'time'
PKG_COLUMN = 'pkg_name'
ANACONDA_BUCKET_PATH = 's3://anaconda-package-data/conda'


def _read_anaconda_parquet(URL, pkg_names=None):
    """Read parquet file in anaconda bucket."""
    storage_options = None
    if 's3://' in URL:
        storage_options = {'anon': True}
    try:
        df = pd.read_parquet(
            URL,
            storage_options=storage_options,
            engine='pyarrow',
            dtype_backend='pyarrow',
        )
        df[TIME_COLUMN] = pd.to_datetime(df[TIME_COLUMN])
        if pkg_names:
            df = df[df[PKG_COLUMN].isin(set(pkg_names))]
    except FileNotFoundError:
        return pd.DataFrame()
    return df


def _anaconda_package_data_by_day(year, month, day, pkg_names=None):
    """Anaconda download data on a per day basis.

    More information: https://github.com/anaconda/anaconda-package-data

    """
    padded_year = '{:04d}'.format(year)
    padded_month = '{:02d}'.format(month)
    padded_day = '{:02d}'.format(day)

    filename = f'{padded_year}-{padded_month}-{padded_day}.parquet'
    URL = f'{ANACONDA_BUCKET_PATH}/hourly/{padded_year}/{padded_month}/{filename}'
    return _read_anaconda_parquet(URL, pkg_names=pkg_names)


def anaconda_package_data_by_year_month(year, month, pkg_names=None):
    """Anaconda download data on a per month basis. Unused.

    More information: https://github.com/anaconda/anaconda-package-data

    """
    padded_year = '{:04d}'.format(year)
    padded_month = '{:02d}'.format(month)
    filename = f'{padded_year}-{padded_month}.parquet'
    URL = f'{ANACONDA_BUCKET_PATH}/monthly/{padded_year}/{filename}'
    return _read_anaconda_parquet(URL, pkg_names=pkg_names)


def _get_previous_anaconda_downloads(output_folder, filename):
    """Read anaconda.csv to get previous downloads."""
    read_csv_kwargs = {
        'parse_dates': [TIME_COLUMN],
    }
    csv_path = get_path(output_folder, filename)
    previous = load_csv(csv_path, read_csv_kwargs=read_csv_kwargs)
    return previous


def _get_downloads_from_anaconda_org(packages, channel='conda-forge'):
    overall_downloads = pd.DataFrame(columns=['pkg_name', TIME_COLUMN, 'total_ndownloads'])
    per_version_downloads = pd.DataFrame(columns=['pkg_name', 'version', TIME_COLUMN, 'ndownloads'])

    for pkg_name in packages:
        URL = f'https://api.anaconda.org/package/{channel}/{pkg_name}'
        timestamp = datetime.now(ZoneInfo('UTC'))
        response = requests.get(URL)
        row_info = {'pkg_name': [pkg_name], TIME_COLUMN: [timestamp], 'total_ndownloads': 0}
        data = response.json()
        total_ndownloads = 0
        if 'could not be found' in data.get('error', ''):
            pass
        else:
            for files_info in data['files']:
                total_ndownloads += files_info['ndownloads']

                per_release_row = {
                    'pkg_name': [pkg_name],
                    'version': [files_info.get('version', None)],
                    TIME_COLUMN: [timestamp],
                    'ndownloads': [files_info.get('ndownloads', 0)],
                }
                per_version_downloads = append_row(per_version_downloads, per_release_row)

            row_info['total_ndownloads'] = total_ndownloads
        overall_downloads = append_row(overall_downloads, row_info)
    return overall_downloads, per_version_downloads


def _collect_ananconda_downloads_from_website(projects, output_folder):
    previous_overall = _get_previous_anaconda_downloads(
        output_folder=output_folder, filename=PREVIOUS_ANACONDA_ORG_OVERALL_FILENAME
    )
    previous_version = _get_previous_anaconda_downloads(
        output_folder=output_folder, filename=PREVIOUS_ANACONDA_ORG_VERSION_FILENAME
    )
    new_overall_downloads, new_version_downloads = _get_downloads_from_anaconda_org(
        projects,
    )
    overall_df = pd.concat([previous_overall, new_overall_downloads], ignore_index=True)
    overall_df = drop_duplicates_by_date(
        overall_df, time_column=TIME_COLUMN, group_by_columns=[PKG_COLUMN]
    )

    version_downloads = pd.concat([previous_version, new_version_downloads], ignore_index=True)
    version_downloads = drop_duplicates_by_date(
        version_downloads, time_column=TIME_COLUMN, group_by_columns=[PKG_COLUMN]
    )
    return overall_df, version_downloads


def collect_anaconda_downloads(
    projects,
    output_folder,
    max_days=90,
    dry_run=False,
    verbose=False,
):
    """Pull data about the downloads of a list of projects from Anaconda.

    Args:
        projects (list[str]):
            List of projects to analyze.
        output_folder (str):
            Folder in which project downloads will be stored.
            It can be passed as a local folder or as a Google Drive path in the format
            `gdrive://{folder_id}`.
            The folder must contain 'anaconda.csv', 'anaconda_org_overall.csv',
            and 'anaconda_org_per_version.csv'.
        max_days (int):
            Maximum amount of days to include in the query from current date back, in case
            `start_date` has not been provided. Defaults to 90 days.
        dry_run (bool):
            If `True`, do not upload the results. Defaults to `False`.
    """
    overall_df, version_downloads = _collect_ananconda_downloads_from_website(
        projects, output_folder=output_folder
    )

    previous = _get_previous_anaconda_downloads(output_folder, filename=PREVIOUS_ANACONDA_FILENAME)
    previous = previous.sort_values(TIME_COLUMN)

    end_date = datetime.now(tz=ZoneInfo('UTC')).date()
    start_date = end_date - timedelta(days=max_days)
    LOGGER.info(f'Getting daily anaconda data for start_date>={start_date} to end_date<{end_date}')
    date_ranges = pd.date_range(start=start_date, end=end_date, freq='D')
    all_downloads_count = len(previous)
    for iteration_datetime in tqdm(date_ranges):
        new_downloads = _anaconda_package_data_by_day(
            year=iteration_datetime.year,
            month=iteration_datetime.month,
            day=iteration_datetime.day,
            pkg_names=projects,
        )
        if len(new_downloads) > 0:
            # Keep only the newest data (on a per day basis) for all packages
            previous = previous[previous[TIME_COLUMN].dt.date != iteration_datetime.date()]
            previous = pd.concat([previous, new_downloads], ignore_index=True)

    previous = previous.sort_values(TIME_COLUMN)
    LOGGER.info('Obtained %s new downloads', all_downloads_count - len(previous))

    if verbose:
        LOGGER.info(f'{PREVIOUS_ANACONDA_FILENAME} tail')
        LOGGER.info(previous.tail(5).to_string())
        LOGGER.info(f'{PREVIOUS_ANACONDA_ORG_OVERALL_FILENAME} tail')
        LOGGER.info(overall_df.tail(5).to_string())
        LOGGER.info(f'{PREVIOUS_ANACONDA_ORG_VERSION_FILENAME} tail')
        LOGGER.info(version_downloads.tail(5).to_string())

    if not dry_run:
        gfolder_path = f'{output_folder}/{PREVIOUS_ANACONDA_FILENAME}'
        create_csv(output_path=gfolder_path, data=previous)

        gfolder_path = f'{output_folder}/{PREVIOUS_ANACONDA_ORG_OVERALL_FILENAME}'
        create_csv(output_path=gfolder_path, data=overall_df)

        gfolder_path = f'{output_folder}/{PREVIOUS_ANACONDA_ORG_VERSION_FILENAME}'
        create_csv(output_path=gfolder_path, data=version_downloads)

    return None
