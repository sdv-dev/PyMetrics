"""Main script."""

import logging
import pathlib

from download_analytics.output import create_csv, load_csv
from download_analytics.pypi import get_pypi_downloads

LOGGER = logging.getLogger(__name__)


def collect_downloads(projects, start_date=None, output_path=None, max_days=1,
                      credentials_file=None, dry_run=False, force=False, backup_path=None):
    """Pull data about the downloads of a list of projects.

    Args:
        projects (Union[list[str], dict[str, list[str]]]):
            List of projects to analyze, or dictionary of collection
            names and lists of projects to analyze.
        start_date (datetime or None):
            Date from which to start collecting data. If `None`,
            start_date will be current date - `max_days`.
        output_path (str):
            Output path, where the CSV will be written.
            It can be passed as a local file, including the `.xlsx` extension,
            or as a Google Drive path in the format `gdrive://{folder_id}/{csv_name}.csv`.
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
        backup_path (str):
            Path to which a backup file must be stored before uploading
            to Google drive.

    Raises:
        TypeError
    """
    if not projects:
        raise ValueError('No projects have been passed')

    if not isinstance(projects, dict):
        if output_path is None:
            raise TypeError('If projects is not a dict, output_path cannot be None')

        projects = {output_path: projects}
        output_path = None

    for csv_path, csv_projects in projects.items():
        if output_path is not None:
            if output_path.startswith('gdrive://'):
                csv_path = f'{output_path}/{csv_path}'
            else:
                csv_path = str(pathlib.Path(output_path) / csv_path)

        if not csv_path.endswith('.csv'):
            csv_path += '.csv'

        previous = load_csv(csv_path)

        pypi_downloads = get_pypi_downloads(
            projects=csv_projects,
            start_date=start_date,
            previous=previous,
            max_days=max_days,
            credentials_file=credentials_file,
            dry_run=dry_run,
            force=force
        )

        if pypi_downloads.empty:
            LOGGER.info('Not creating empty CSV file %s', csv_path)
        elif pypi_downloads.equals(previous):
            LOGGER.info('Skipping update of unmodified CSV file %s', csv_path)
        else:
            if backup_path:
                create_csv(backup_path, pypi_downloads)

            create_csv(csv_path, pypi_downloads)
