"""Functions to compute aggregation metrics over raw downloads."""

import logging

import numpy as np
import pandas as pd
from packaging.version import InvalidVersion, Version

from pymetrics.output import create_spreadsheet

LOGGER = logging.getLogger(__name__)


def _groupby(downloads, groupby, index_name=None, percent=True):
    grouped = downloads.groupby(groupby, dropna=False).size().reset_index()
    grouped.columns = [index_name or groupby, 'downloads']
    if percent:
        grouped['percent'] = (grouped.downloads * 100 / grouped.downloads.sum()).round(3)

    return grouped


def _by_month(downloads):
    year_month = downloads.timestamp.dt.strftime('%Y-%m')
    by_month = _groupby(downloads, year_month, 'year-month', percent=False)
    by_month['increase'] = by_month.downloads.diff()
    return by_month.iloc[::-1]


def _historical_groupby(downloads, groupbys=None):
    year_month = downloads.timestamp.dt.strftime('%Y-%m')
    base = downloads.groupby(year_month).size().to_frame()
    base.index.name = 'year-month'
    base.columns = ['total']

    if groupbys is None:
        groupbys = downloads.set_index('timestamp').columns

    new_columns = []
    for groupby in groupbys:
        grouped = downloads.groupby([year_month, groupby])
        grouped_sizes = grouped.size().unstack(-1)  # noqa: PD010
        if len(groupbys) > 1:
            grouped_sizes.columns = f"{groupby}='" + grouped_sizes.columns + "'"
        new_columns.append(grouped_sizes.fillna(0))

    if new_columns:
        base = pd.concat([base] + new_columns, axis=1)

    totals = base.sum()
    totals.name = 'total'
    base = pd.concat([base, totals.to_frame().T], ignore_index=True)

    return base.reset_index().iloc[::-1]


def _get_sheet_name(column):
    words = [f'{word[0].upper()}{word[1:]}' for word in column.split('_')]
    return ' '.join(['By'] + words)


RENAME_COLUMNS = {
    'implementation_name': 'python_implementation',
    'implementation_version': 'python_version',
    'system_release': 'distro_kernel',
    'system_name': 'OS_type',
}
GROUPBY_COLUMNS = [
    # 'project',
    'version',
    'country_code',
    'python_version',
    'full_python_version',
    # 'python_implementation',
    'installer_name',
    # 'type',
    'distro_name',
    'distro_version',
    'distro_kernel',
    'OS_type',
    'cpu',
    'ci',
]
SORT_BY_DOWNLOADS = [
    'country_code',
    # 'project',
    'type',
    'installer_name',
    'python_implementation',
    'python_version',
    'distro_name',
    'distro_version',
    'distro_kernel',
    'OS_type',
    'cpu',
]
SORT_BY_VERSION = [
    'version',
    'full_python_version',
]
HISTORICAL_COLUMNS = [
    'version',
    'python_version',
    'country_code',
    'installer_name',
]


def _mangle_columns(downloads):
    downloads = downloads.rename(columns=RENAME_COLUMNS)
    for col in [
        'python_version',
        'project',
        'version',
        'distro_name',
        'distro_version',
        'distro_kernel',
    ]:
        downloads[col] = downloads[col].astype('string')

    downloads['full_python_version'] = downloads['python_version']
    downloads['python_version'] = downloads['python_version'].str.rsplit('.', n=1).str[0]
    downloads['project_version'] = downloads['project'] + '-' + downloads['version']
    downloads['distro_version'] = downloads['distro_name'] + ' ' + downloads['distro_version']
    downloads['distro_kernel'] = downloads['distro_version'] + ' - ' + downloads['distro_kernel']

    return downloads


def _safe_version_parse(version_str):
    if pd.isna(version_str):
        return np.nan

    try:
        version = Version(str(version_str))
    except InvalidVersion:
        cleaned = str(version_str).rstrip('+~')
        try:
            version = Version(cleaned)
        except (InvalidVersion, TypeError):
            LOGGER.info(f'Unable to parse version: {version_str}')
            version = np.nan

    return version


def _version_order_key(version_column):
    return version_column.apply(_safe_version_parse)


def _sort_by_version(data, column, ascending=False):
    data = data.sort_values(by=column, key=_version_order_key, ascending=ascending)
    return data


def compute_metrics(downloads, output_path=None):
    """Compute aggregation metrics over the given downloads.

    The computed metrics are stored in a spreadsheet file
    in the path ``{output_folder}/{project}.xlsx``.
    """
    downloads = _mangle_columns(downloads)

    LOGGER.debug('Aggregating by month')
    sheets = {'By Month': _by_month(downloads)}

    for column in GROUPBY_COLUMNS:
        name = _get_sheet_name(column)
        LOGGER.debug('Aggregating by %s', column)
        sheet = _groupby(downloads, column)
        if column in SORT_BY_DOWNLOADS:
            sheet = sheet.sort_values('downloads', ascending=False)
        elif column in SORT_BY_VERSION:
            sheet = _sort_by_version(sheet, column=column, ascending=False)
        sheets[name] = sheet

    for column in HISTORICAL_COLUMNS:
        LOGGER.debug('Aggregating by month and %s', column)
        name = 'Month and ' + _get_sheet_name(column)
        sheets[name] = _historical_groupby(downloads, [column])

    if output_path:
        create_spreadsheet(output_path, sheets, na_rep='<NaN>')
        return None

    return sheets
