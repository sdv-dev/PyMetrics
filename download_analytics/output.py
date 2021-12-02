"""Functions to create the output spreadsheet."""

import io
import logging
import pathlib

import pandas as pd

from download_analytics import drive

LOGGER = logging.getLogger(__name__)

DATE_COLUMNS = [
    'created_at',
    'updated_at',
    'closed_at',
    'starred_at',
    'user_created_at',
    'user_updated_at',
]


def _add_sheet(writer, data, sheet):
    data.to_excel(writer, sheet_name=sheet, index=False)

    for column in data:
        column_width = max(data[column].astype(str).map(len).max(), len(column))
        col_idx = data.columns.get_loc(column)
        writer.sheets[sheet].set_column(col_idx, col_idx, column_width + 2)


def create_spreadsheet(output_path, sheets):
    """Create a spreadsheet with the indicated name and data.

    If the ``output_path`` variable ends in ``xlsx`` it is interpreted as
    a path to where the file must be created. Otherwise, it is interpreted
    as a name to use when constructing the final filename, which will be
    ``github-metrics-{name}-{today}.xlsx`` within the current working
    directory.

    The ``sheets`` must be passed as as dictionary that contains sheet
    titles as keys and sheet contents as values, passed as pandas.DataFrames.

    Args:
        output_path (str or stream):
            Path to where the file must be created, or open stream to write to.
        sheets (dict[str, pandas.DataFrame]):
            Sheets to created, passed as a dict that contains sheet titles as
            keys and sheet contents as values, passed as pandas.DataFrames.
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:  # pylint: disable=E0110
        for title, data in sheets.items():
            _add_sheet(writer, data, title)

    if drive.is_drive_path(output_path):
        LOGGER.info('Creating file %s', output_path)
        folder, filename = drive.split_drive_path(output_path)
        drive.upload(output, filename, folder)
    else:
        if not output_path.endswith('.xlsx'):
            output_path += '.xlsx'

        LOGGER.info('Creating file %s', output_path)
        output_path = pathlib.Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(output.getbuffer())


def create_csv(output_path, data):
    """Create a CSV with the indicated name and data.

    Args:
        output_path (str or stream):
            Path to where the file must be created, or open stream to write to.
        data (dict[str, pandas.DataFrame]):
            Sheets to created, passed as a dict that contains sheet titles as
            keys and sheet contents as values, passed as pandas.DataFrames.
    """
    output = io.BytesIO()
    data.to_csv(output, index=False)

    if not output_path.endswith('.csv'):
        output_path += '.csv'

    LOGGER.info('Creating file %s', output_path)

    if drive.is_drive_path(output_path):
        folder, filename = drive.split_drive_path(output_path)
        drive.upload(output, filename, folder)
    else:
        output_path = pathlib.Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(output.getbuffer())


def load_spreadsheet(spreadsheet):
    """Load a spreadsheet previously created by download-analytics.

    Args:
        spreadsheet (str or stream):
            Path to where the file is stored, or open stream
            to read from.

    Return:
        dict[str, pd.DataFrame]:
            Dict of strings and dataframes with the contents
            of the spreadsheet and the date fields properly
            parsed to datetimes.
    """
    LOGGER.info('Trying to load spreadsheet %s', spreadsheet)
    if drive.is_drive_path(spreadsheet):
        path = spreadsheet
        folder, filename = drive.split_drive_path(spreadsheet)
        spreadsheet = drive.download(folder, filename)
    else:
        if not spreadsheet.endswith('.xlsx'):
            spreadsheet += '.xlsx'

        path = spreadsheet

    sheets = pd.read_excel(spreadsheet, sheet_name=None)
    for sheet in sheets.values():  # noqa
        for column in DATE_COLUMNS:
            if column in sheet:
                sheet[column] = pd.to_datetime(sheet[column], utc=True).dt.tz_convert(None)

    LOGGER.info('Loaded spreadsheet %s', path)

    return sheets


def load_csv(csv_path):
    """Load a CSV previously created by download-analytics.

    Args:
        csv_path (str):
            Path to where the file is stored.

    Return:
        pd.DataFrame:
            CSV contents.
    """
    if not csv_path.endswith('.csv'):
        csv_path += '.csv'

    LOGGER.info('Trying to load CSV file %s', csv_path)
    try:
        if drive.is_drive_path(csv_path):
            folder, filename = drive.split_drive_path(csv_path)
            stream = drive.download(folder, filename)
            data = pd.read_csv(stream, parse_dates=['timestamp'])
        else:
            data = pd.read_csv(csv_path, parse_dates=['timestamp'])

    except FileNotFoundError:
        LOGGER.info('Failed to load CSV file %s: not found', csv_path)
        return None

    LOGGER.info('Loaded CSV %s', csv_path)

    return data
