"""Functions to query Google Big Query."""

# pylint: disable=E1101

import json
import logging
import os
import pathlib
import pandas as pd

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

    if os.path.exists(credentials_contents):
        credentials = service_account.Credentials.from_service_account_file(
            credentials_contents,
            scopes=['https://www.googleapis.com/auth/cloud-platform'],
        )
    else:
        service_account_info = json.loads(credentials_contents)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/cloud-platform'],
        )

    return bigquery.Client(
        credentials=credentials,
        project=credentials.project_id,
    )


def run_query(query, dry_run=False, credentials_file=None):
    """Run a BigQuery query and return the query_job object."""
    client = _get_bq_client(credentials_file)

    LOGGER.debug('Running query %s', query)

    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    dry_run_job = client.query(query, job_config=job_config)
    LOGGER.info('Estimated data processed in query (GBs): %.2f', dry_run_job.total_bytes_processed / 1024**3)
    # https://cloud.google.com/bigquery/pricing#on_demand_pricing
    # assuming have hit 1 terabyte processed in month
    cost_per_terabyte = 6.15
    bytes = dry_run_job.total_bytes_processed
    cost = cost_per_terabyte * bytes_to_terabytes(bytes)
    LOGGER.info('Estimated cost for query: $%.2f', cost)

    if dry_run:
        return None

    query_job = client.query(query)
    data = query_job.to_dataframe()
    LOGGER.info('Total processed GBs: %.2f', query_job.total_bytes_processed / 1024**3)
    LOGGER.info('Total billed GBs: %.2f', query_job.total_bytes_billed / 1024**3)
    cost = cost_per_terabyte * bytes_to_terabytes(query_job.total_bytes_billed)
    LOGGER.info('Total cost for query: $%.2f', cost)
    return data

def bytes_to_megabytes(bytes):
    return bytes / 1024 / 1024

def bytes_to_gigabytes(bytes):
    return bytes_to_megabytes(bytes) / 1024

def bytes_to_terabytes(bytes):
    return bytes_to_gigabytes(bytes) / 1024
