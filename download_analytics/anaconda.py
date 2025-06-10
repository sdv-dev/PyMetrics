import logging
from datetime import date, timedelta
from functools import lru_cache

import boto3
import pandas as pd
from botocore import UNSIGNED
from botocore.client import Config
from tqdm import tqdm

from download_analytics.output import get_path
from download_analytics.pypi import _get_query_dates

LOGGER = logging.getLogger(__name__)


BUCKET_NAME = "anaconda-package-data"
PREVIOUS_FILENAME = "anaconda.csv"
TIME_COLUMN = 'time'
PKG_COLUMN = 'pkg_name'


def get_all_s3_keys(bucket):
    keys = []
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    kwargs = {'Bucket': bucket}
    while True:
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp['Contents']:
            keys.append(obj['Key'])
        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break
    return keys


@lru_cache()
def all_files():
    all_keys = get_all_s3_keys("anaconda-package-data")
    all_keys = [x for x in all_keys if x.endswith("parquet")]
    hourly_files = [x for x in all_keys if "hourly" in x]
    monthly_files = [x for x in all_keys if "monthly" in x]
    return hourly_files, monthly_files


def read_anaconda_parquet(URL, pkg_names=None):
    storage_options = None
    if 's3://' in URL:
        storage_options = {"anon": True}
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


def anaconda_package_data_by_day(year, month, day, pkg_names=None):
    padded_year = "{:04d}".format(year)
    padded_month = "{:02d}".format(month)
    padded_day = "{:02d}".format(day)

    filename = f"{padded_year}-{padded_month}-{padded_day}.parquet"
    URL = f"s3://anaconda-package-data/conda/hourly/{padded_year}/{padded_month}/{filename}"
    return read_anaconda_parquet(URL, pkg_names=pkg_names)


def anaconda_package_data_by_year_month(year, month, pkg_names=None):
    padded_year = "{:04d}".format(year)
    padded_month = "{:02d}".format(month)
    filename = f"{padded_year}-{padded_month}.parquet"
    URL = f"s3://anaconda-package-data/conda/monthly/{padded_year}/{filename}"
    return read_anaconda_parquet(URL, pkg_names=pkg_names)


def get_downloads(input_file, output_folder, dry_run):
    if input_file:
        downloads = pd.read_csv(input_file, parse_dates=[TIME_COLUMN])
    else:
        csv_path = get_path(output_folder, PREVIOUS_FILENAME)
        downloads = pd.read_csv(csv_path, parse_dates=[TIME_COLUMN])
    return downloads


def daterange(start_date: date, end_date: date):
    days = int((end_date - start_date).days)
    for n in range(days):
        yield start_date + timedelta(n)


def collect_anaconda_downloads(
    projects,
    output_folder,
    max_days=60,
    start_date=None,
    end_date=None,
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
    previous = get_downloads(input_file, output_folder, dry_run)

    previous_projects = previous[previous[PKG_COLUMN].isin(set(projects))]
    min_date = previous[TIME_COLUMN].min().date()
    max_date = previous_projects[TIME_COLUMN].max().date()

    start_date, end_date = _get_query_dates(start_date, min_date,
                                            max_date,
                                            max_days)

    date_ranges = pd.date_range(start=start_date,
                                end=end_date,
                                freq='D')

    for date in tqdm(date_ranges):
        new_downloads = anaconda_package_data_by_day(
            year=date.year,
            month=date.month,
            day=date.day,
            pkg_names=projects
        )
        if len(new_downloads) > 0:
            before = previous[previous[TIME_COLUMN] < new_downloads[TIME_COLUMN].min()]
            after = new_downloads
            previous = pd.concat([before, after], ignore_index=True)

    LOGGER.info('Obtained %s new downloads', len(all_downloads) - len(previous))
    return previous
