"""Main script."""

import logging
import pathlib

from download_analytics.output import create_spreadsheet, load_spreadsheet
from download_analytics.pypi import get_pypi_downloads

LOGGER = logging.getLogger(__name__)


def collect_downloads(projects, start_date=None, output_path=None, max_days=1,
                      credentials_file=None, dry_run=False, force=False):
    """Pull data about the downloads of a list of projects.

    Args:
        projects (Union[list[str], dict[str, list[str]]]):
            List of projects to analyze, or dictionary of collection
            names and lists of projects to analyze.
        start_date (datetime or None):
            Date from which to start collecting data. If `None`,
            start_date will be current date - `max_days`.
        output_path (str):
            Output path, where the spreadsheet will be written.
            It can be passed as a local file, including the `.xlsx` extension,
            or as a Google Drive path in the format `gdrive://{folder_id}/{spreadsheet_name}`.
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
        dict[str, pd.DataFrame] or None:
            If output_path is None, a dict with the sheets is returned.

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

    for spreadsheet_path, spreadsheet_projects in projects.items():
        if output_path is not None:
            if output_path.startswith('gdrive://'):
                spreadsheet_path = f'{output_path}/{spreadsheet_path}'
            else:
                spreadsheet_path = str(pathlib.Path(output_path) / spreadsheet_path)

        try:
            previous = load_spreadsheet(spreadsheet_path)
        except FileNotFoundError:
            previous = {'PyPI': None}

        pypi_downloads = get_pypi_downloads(
            projects=spreadsheet_projects,
            start_date=start_date,
            previous=previous['PyPI'],
            max_days=max_days,
            credentials_file=credentials_file,
            dry_run=dry_run,
            force=force
        )

        sheets = {
            'PyPI': pypi_downloads,
        }

        create_spreadsheet(spreadsheet_path, sheets)
