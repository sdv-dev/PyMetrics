"""Functions to get Anaconda downloads from Anaconda S3 bucket."""

import logging
from datetime import datetime, timedelta, timezone

import pandas as pd
from tqdm import tqdm
import requests
from zoneinfo import ZoneInfo
from datetime import datetime
from download_analytics.output import create_spreadsheet, append_row, get_path, load_csv



for pkg in PKG_NAMES:
    URL = f'https://api.anaconda.org/package/conda-forge/{pkg}'
    response = requests.get(URL)
    row_info = {
        'pkg_name': [pkg],
        'timestamp': [datetime.now(ZoneInfo("America/New_York"))],
    }
    data = response.json()
    downloads = 0
    if 'error' in data and 'could not be found' in data['error']:
        row_info['total_ndownloads'] = downloads
    else:
        for files_info in data['files']:
            downloads += files_info['ndownloads']
        row_info['total_ndownloads'] = downloads
    projects_metadata = append_row(projects_metadata, row_info)
from download_analytics.output import get_path

LOGGER = logging.getLogger(__name__)


BUCKET_NAME = 'anaconda-package-data'
PREVIOUS_FILENAME = 'anaconda.csv'
TIME_COLUMN = 'time'
PKG_COLUMN = 'pkg_name'


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
    URL = f's3://anaconda-package-data/conda/hourly/{padded_year}/{padded_month}/{filename}'
    return _read_anaconda_parquet(URL, pkg_names=pkg_names)


def anaconda_package_data_by_year_month(year, month, pkg_names=None):
    """Anaconda download data on a per month basis. Unused.

    More information: https://github.com/anaconda/anaconda-package-data

    """
    padded_year = '{:04d}'.format(year)
    padded_month = '{:02d}'.format(month)
    filename = f'{padded_year}-{padded_month}.parquet'
    URL = f's3://anaconda-package-data/conda/monthly/{padded_year}/{filename}'
    return _read_anaconda_parquet(URL, pkg_names=pkg_names)


def _get_previous_anaconda_downloads(input_file, output_folder):
    """Read anaconda.csv to get previous downloads."""
    LOGGER.info(f'Loading previous anaconda downloads: {input_file}')
    csv_path = input_file or get_path(output_folder, PREVIOUS_FILENAME)
    LOGGER.info('Loaded previous anaconda downloads')
    return pd.read_csv(csv_path, parse_dates=[TIME_COLUMN])


def _get_downloads_from_anaconda_org(packages,
                                     channel='conda-forge'):
    downloads_df = pd.DataFrame(
        columns=['pkg_name', 'timestamp', 'total_ndownloads']
    )

    for pkg_name in packages:
        URL = f'https://api.anaconda.org/package/{channel}/{pkg_name}'
        response = requests.get(URL)
        row_info = {
            'pkg_name': [pkg_name],
            'timestamp': [datetime.now(ZoneInfo("America/New_York"))],
        }
        data = response.json()
        downloads = 0
        if 'could not be found' in data.get('error', ''):
            row_info['total_ndownloads'] = downloads
        else:
            for files_info in data['files']:
                downloads += files_info['ndownloads']
            row_info['total_ndownloads'] = downloads
        downloads_df = append_row(downloads_df, row_info)
    return downloads_df

def _collect_ananconda_downloads_from_website(projects):
    previous =
    downloads_df = _get_downloads_from_anaconda_org(
        projects
    )

def collect_anaconda_downloads(
    projects,
    output_folder,
    max_days=60,
    previous=None,
    input_file=None,
    dry_run=False,
):
    """Pull data about the downloads of a list of projects from Anaconda.

    Args:
        projects (list[str]):
            List of projects to analyze.
        output_folder (str):
            Folder in which project downloads will be stored.
            It can be passed as a local folder or as a Google Drive path in the format
            `gdrive://{folder_id}`.
        max_days (int):
            Maximum amount of days to include in the query from current date back, in case
            `start_date` has not been provided. Defaults to 1.
        dry_run (bool):
            If `True`, do not run the actual query. Defaults to `False`.
    """


    previous = _get_previous_anaconda_downloads(input_file, output_folder)
    previous = previous.sort_values(TIME_COLUMN)

    end_date = datetime.now(tz=None).date()
    start_date = end_date - timedelta(days=max_days)
    LOGGER.info(f'Getting daily anaconda downloads for start_date>={start_date} to end_date<{end_date}')
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
            # Keep only the newest data (on a per day basis)
            previous = previous[previous[TIME_COLUMN].dt.date != iteration_datetime.date()]
            previous = pd.concat([previous, new_downloads], ignore_index=True)

    previous = previous.sort_values(TIME_COLUMN)
    LOGGER.info('Obtained %s new downloads', all_downloads_count - len(previous))
    return previous
