"""Functions to query Google Big Query."""

# pylint: disable=E1101

import json
import logging
import os
import pathlib

from google.cloud import bigquery
from google.oauth2 import service_account

LOGGER = logging.getLogger(__name__)


def _get_bq_client(credentials_file):
    if credentials_file:
        LOGGER.info('Loading BigQuery credentials from %s', credentials_file)
        credentials_contents = pathlib.Path(credentials_file).read_text()
    else:
        credentials_contents = os.getenv('BIGQUERY_CREDENTIALS')
        if not credentials_contents:
            raise ValueError('No GCP Service Account info provided.')

        LOGGER.info('Loading BigQuery credentials from BIGQUERY_CREDENTIALS envvar')

    service_account_info = json.loads(credentials_contents)
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=['https://www.googleapis.com/auth/cloud-platform'],
    )

    return bigquery.Client(credentials=credentials, project=credentials.project_id,)


def run_query(query, dry_run=False, credentials_file=None):
    """Run a BigQuery query and return the query_job object."""
    client = _get_bq_client(credentials_file)

    LOGGER.debug('Running query %s', query)

    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    dry_run_job = client.query(query, job_config=job_config)
    LOGGER.info('Estimated processed GBs: %.2f', dry_run_job.total_bytes_processed / 1024 ** 3)

    if dry_run:
        return None

    query_job = client.query(query)
    data = query_job.to_dataframe()
    LOGGER.info('Total processed GBs: %.2f', query_job.total_bytes_processed / 1024 ** 3)
    LOGGER.info('Total billed GBs: %.2f', query_job.total_bytes_billed / 1024 ** 3)

    return data
