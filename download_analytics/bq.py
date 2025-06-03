"""Functions to query Google Big Query."""

# pylint: disable=E1101

import json
import logging
import os
import pathlib

import pandas as pd
import pyarrow as pa
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
        LOGGER.info('Loading BigQuery credentials from service account file')
        credentials = service_account.Credentials.from_service_account_file(
            credentials_contents,
            scopes=['https://www.googleapis.com/auth/cloud-platform'],
        )
    else:
        LOGGER.info('Loading BigQuery credentials from service account info')
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
    data_processed_gbs = dry_run_job.total_bytes_processed / 1024**3
    LOGGER.info('Estimated data processed in query (GBs): %.2f', data_processed_gbs)
    # https://cloud.google.com/bigquery/pricing#on_demand_pricing
    # assuming have hit 1 terabyte processed in month
    cost_per_terabyte = 6.15
    bytes = dry_run_job.total_bytes_processed
    cost = cost_per_terabyte * bytes_to_terabytes(bytes)
    LOGGER.info('Estimated cost for query: $%.2f', cost)

    if dry_run:
        return None

    query_job = client.query(query)
    dataframe_args = {
        'create_bqstorage_client': True,
        'bool_dtype': pd.ArrowDtype(pa.bool_()),
        'int_dtype': pd.ArrowDtype(pa.int64()),
        'float_dtype': pd.ArrowDtype(pa.float64()),
        'string_dtype': pd.ArrowDtype(pa.string()),
        'timestamp_dtype': pd.ArrowDtype(pa.timestamp('ns', tz='UTC')),
    }
    data = query_job.to_dataframe(**dataframe_args)
    LOGGER.info('Total processed GBs: %.2f', query_job.total_bytes_processed / 1024**3)
    LOGGER.info('Total billed GBs: %.2f', query_job.total_bytes_billed / 1024**3)
    cost = cost_per_terabyte * bytes_to_terabytes(query_job.total_bytes_billed)
    LOGGER.info('Total cost for query: $%.2f', cost)
    return data


def bytes_to_megabytes(bytes):
    """Convert bytes to megabytes."""
    return bytes / 1024 / 1024


def bytes_to_gigabytes(bytes):
    """Convert bytes to gigabytes."""
    return bytes_to_megabytes(bytes) / 1024


def bytes_to_terabytes(bytes):
    """Convert bytes to terabytes."""
    return bytes_to_gigabytes(bytes) / 1024
