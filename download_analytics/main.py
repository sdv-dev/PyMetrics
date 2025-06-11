"""Main script."""
import pandas as pd
import logging

from download_analytics.metrics import compute_metrics
from download_analytics.output import create_csv, get_path, load_csv
from download_analytics.pypi import get_pypi_downloads

LOGGER = logging.getLogger(__name__)


def collect_downloads(
    projects,
    output_folder,
    start_date=None,
    max_days=1,
    credentials_file=None,
    dry_run=False,
    force=False,
    add_metrics=True,
):
    """Pull data about the downloads of a list of projects.

    Args:
        projects (list[str]):
            List of projects to analyze.
        output_folder (str):
            Folder in which project downloads will be stored.
            It can be passed as a local folder or as a Google Drive path in the format
            `gdrive://{folder_id}`.
        start_date (datetime or None):
            Date from which to start collecting data. If `None`,
            start_date will be current date - `max_days`.
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
        add_metrics (bool):
            Whether to compute and create the aggregation metrics spreadsheets.
    """
    if not projects:
        raise ValueError('No projects have been passed')

    LOGGER.info(f'Collecting downloads for projects={projects}')

    csv_path = get_path(output_folder, 'pypi.csv')
    read_csv_kwargs = {
        'parse_dates': ['timestamp'],
        'dtype': {
            'country_code': pd.CategoricalDtype(),
            'project': pd.CategoricalDtype(),
            'version': pd.CategoricalDtype(),
            'type': pd.CategoricalDtype(),
            'installer_name': pd.CategoricalDtype(),
            'implementation_name': pd.CategoricalDtype(),
            'implementation_version': pd.CategoricalDtype(),
            'distro_name': pd.CategoricalDtype(),
            'distro_version': pd.CategoricalDtype(),
            'system_name': pd.CategoricalDtype(),
            'system_release': pd.CategoricalDtype(),
            'cpu': pd.CategoricalDtype(),
        },
    }
    previous = load_csv(csv_path, dry_run=dry_run, read_csv_kwargs=read_csv_kwargs)

    pypi_downloads = get_pypi_downloads(
        projects=projects,
        start_date=start_date,
        previous=previous,
        max_days=max_days,
        credentials_file=credentials_file,
        dry_run=dry_run,
        force=force,
    )

    if pypi_downloads.empty:
        LOGGER.info('Not creating empty CSV file %s', csv_path)
    elif pypi_downloads.equals(previous):
        msg = f'Skipping update of unmodified CSV file {csv_path}'
        if dry_run:
            msg += f' because dry_run={dry_run}, meaning no downloads were returned from BigQuery'
        LOGGER.info(msg)

    else:
        create_csv(csv_path, pypi_downloads)

    if add_metrics:
        for project in projects:
            project_downloads = pypi_downloads[pypi_downloads.project == project]
            if not project_downloads.empty:
                LOGGER.info('Computing metrics for project %s', project)
                output_path = get_path(output_folder, project)
                if dry_run:
                    output_path = None

                compute_metrics(project_downloads, output_path)
