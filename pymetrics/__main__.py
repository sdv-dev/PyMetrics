"""PyMetrics CLI."""

import argparse
import logging
import pathlib
import sys
import warnings
from datetime import datetime

import yaml

from pymetrics.anaconda import collect_anaconda_downloads
from pymetrics.gh_downloads import collect_github_downloads
from pymetrics.main import collect_pypi_downloads
from pymetrics.summarize import summarize_downloads

LOGGER = logging.getLogger(__name__)


def _env_setup(logfile, verbosity):
    warnings.simplefilter('ignore')

    format_ = '%(asctime)s - %(levelname)s - %(message)s'
    level = (3 - verbosity) * 10
    logging.basicConfig(filename=logfile, level=level, format=format_)
    logging.getLogger('pymetrics').setLevel(level)
    logging.getLogger().setLevel(logging.WARN)


def _load_config(config_path):
    config_path = pathlib.Path(config_path)
    if not config_path.exists():
        return {}

    config = yaml.safe_load(config_path.read_text())
    import_config = config.pop('import_config', None)
    if import_config:
        import_config_path = pathlib.Path(import_config)
        if import_config_path.is_absolute():
            import_config_path = config_path.parent / import_config_path

        import_config = _load_config(import_config_path)
        import_config.update(config)
        config = import_config

    return config


def _collect_pypi(args):
    config = _load_config(args.config_file)
    projects = args.projects or config['projects']
    output_folder = args.output_folder
    max_days = args.max_days

    collect_pypi_downloads(
        projects=projects,
        start_date=args.start_date,
        output_folder=output_folder,
        max_days=max_days,
        credentials_file=args.authentication_credentials,
        dry_run=args.dry_run,
        force=args.force,
        add_metrics=args.add_metrics,
    )


def _collect_anaconda(args):
    config = _load_config(args.config_file)
    projects = config['projects']
    output_folder = args.output_folder
    collect_anaconda_downloads(
        projects=projects,
        output_folder=output_folder,
        max_days=args.max_days,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )


def _collect_github(args):
    config = _load_config(args.config_file)
    projects = config['projects']
    output_folder = args.output_folder

    collect_github_downloads(
        projects=projects,
        output_folder=output_folder,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )


def _summarize(args):
    config = _load_config(args.config_file)
    projects = config['projects']
    vendors = config['vendors']
    output_folder = args.output_folder

    summarize_downloads(
        projects=projects,
        vendors=vendors,
        output_folder=output_folder,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )


def _valid_date(arg):
    try:
        return datetime.strptime(arg, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f'Invalid date: {arg}') from None


def _get_parser():
    # Logging
    logging_args = argparse.ArgumentParser(add_help=False)
    logging_args.add_argument(
        '-v',
        '--verbose',
        action='count',
        default=0,
        help='Be verbose. Use `-vv` for increased verbosity.',
    )
    logging_args.add_argument(
        '-l', '--logfile', help='If given, file where the logs will be written.'
    )
    logging_args.add_argument(
        '-d',
        '--dry-run',
        action='store_true',
        help='Do not upload the results. Just calculate them.',
    )
    parser = argparse.ArgumentParser(
        prog='pymetrics',
        description='PyMetrics Command Line Interface',
        parents=[logging_args],
    )
    parser.set_defaults(action=None)
    action = parser.add_subparsers(title='action')
    action.required = True

    # collect PyPI
    collect_pypi = action.add_parser(
        'collect-pypi', help='Collect download data from PyPi.', parents=[logging_args]
    )
    collect_pypi.set_defaults(action=_collect_pypi)

    collect_pypi.add_argument(
        '-o',
        '--output-folder',
        type=str,
        required=True,
        help=(
            'Path to the folder where data will be stored. It can be a local path or a'
            ' Google Drive folder path in the format gdrive://<folder-id>'
        ),
    )
    collect_pypi.add_argument(
        '-a',
        '--authentication-credentials',
        type=str,
        required=False,
        help='Path to the GCP (BigQuery) credentials file to use.',
    )
    collect_pypi.add_argument(
        '-c',
        '--config-file',
        type=str,
        default='config.yaml',
        help='Path to the configuration file.',
    )
    collect_pypi.add_argument(
        '-p',
        '--projects',
        nargs='*',
        help='List of projects to collect. If not given use the configured ones.',
        default=None,
    )
    collect_pypi.add_argument(
        '-s',
        '--start-date',
        type=_valid_date,
        required=False,
        help='Date from which to start pulling data.',
    )
    collect_pypi.add_argument(
        '-m',
        '--max-days',
        type=int,
        required=False,
        help='Max days of data to pull if start-date is not given',
    )
    collect_pypi.add_argument(
        '-f',
        '--force',
        action='store_true',
        help='Force the download even if the data already exists or there is a gap',
    )
    collect_pypi.add_argument(
        '-M',
        '--add-metrics',
        action='store_true',
        help='Compute the aggregation metrics and create the corresponding spreadsheets.',
    )

    # summarize
    summarize = action.add_parser(
        'summarize', help='Summarize the downloads data.', parents=[logging_args]
    )
    summarize.set_defaults(action=_summarize)
    summarize.add_argument(
        '-c',
        '--config-file',
        type=str,
        default='summarize_config.yaml',
        help='Path to the configuration file.',
    )
    summarize.add_argument(
        '-o',
        '--output-folder',
        type=str,
        required=True,
        help=(
            'Path to the folder where data will be pypi.csv exists. It can be a local path or a'
            ' Google Drive folder path in the format gdrive://<folder-id>'
        ),
    )

    # collect Anaconda
    collect_anaconda = action.add_parser(
        'collect-anaconda', help='Collect download data from Anaconda.', parents=[logging_args]
    )
    collect_anaconda.set_defaults(action=_collect_anaconda)
    collect_anaconda.add_argument(
        '-c',
        '--config-file',
        type=str,
        default='config.yaml',
        help='Path to the configuration file.',
    )
    collect_anaconda.add_argument(
        '-o',
        '--output-folder',
        type=str,
        required=True,
        help=(
            'Path to the folder where data will be outputted. It can be a local path or a'
            ' Google Drive folder path in the format gdrive://<folder-id>'
        ),
    )
    collect_anaconda.add_argument(
        '-m',
        '--max-days',
        type=int,
        required=False,
        default=90,
        help='Max days of data to pull. Default to last 90 days.',
    )

    # collect Anaconda
    collect_github = action.add_parser(
        'collect-github', help='Collect download data from GitHub.', parents=[logging_args]
    )
    collect_github.set_defaults(action=_collect_github)
    collect_github.add_argument(
        '-c',
        '--config-file',
        type=str,
        default='config.yaml',
        help='Path to the configuration file.',
    )
    collect_github.add_argument(
        '-o',
        '--output-folder',
        type=str,
        required=True,
        help=(
            'Path to the folder where data will be outputted. It can be a local path or a'
            ' Google Drive folder path in the format gdrive://<folder-id>'
        ),
    )
    return parser


def main():
    """Run the PyMetrics CLI."""
    parser = _get_parser()
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    _env_setup(args.logfile, args.verbose)
    args.action(args)


if __name__ == '__main__':
    main()
