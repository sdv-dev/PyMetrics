"""Download Analytics CLI."""

import argparse
import logging
import pathlib
import sys
import warnings
from datetime import datetime

import yaml

from download_analytics.main import collect_downloads

LOGGER = logging.getLogger(__name__)


def _env_setup(logfile, verbosity):
    warnings.simplefilter('ignore')

    format_ = '%(asctime)s - %(levelname)s - %(message)s'
    level = (3 - verbosity) * 10
    logging.basicConfig(filename=logfile, level=level, format=format_)
    logging.getLogger('download_analytics').setLevel(level)
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


def _collect(args):
    config = _load_config(args.config_file)
    projects = args.projects or config['projects']
    output_folder = args.output_folder or config.get('output-folder', '.')
    max_days = args.max_days or config.get('max-days')

    collect_downloads(
        projects=projects,
        start_date=args.start_date,
        output_folder=output_folder,
        max_days=max_days,
        credentials_file=args.authentication_credentials,
        dry_run=args.dry_run,
        force=args.force,
        add_metrics=args.add_metrics,
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

    parser = argparse.ArgumentParser(
        prog='download-analytics',
        description='Download Analytics Command Line Interface',
        parents=[logging_args],
    )
    parser.set_defaults(action=None)
    action = parser.add_subparsers(title='action')
    action.required = True

    # collect
    collect = action.add_parser('collect', help='Collect downloads data.', parents=[logging_args])
    collect.set_defaults(action=_collect)

    collect.add_argument(
        '-o',
        '--output-folder',
        type=str,
        required=False,
        help=(
            'Path to the folder where data will be stored. It can be a local path or a'
            ' Google Drive folder path in the format gdrive://<folder-id>'
        ),
    )
    collect.add_argument(
        '-a',
        '--authentication-credentials',
        type=str,
        required=False,
        help='Path to the GCP (BigQuery) credentials file to use.',
    )
    collect.add_argument(
        '-c',
        '--config-file',
        type=str,
        default='config.yaml',
        help='Path to the configuration file.',
    )
    collect.add_argument(
        '-p',
        '--projects',
        nargs='*',
        help='List of projects to collect. If not given use the configured ones.',
        default=None,
    )
    collect.add_argument(
        '-s',
        '--start-date',
        type=_valid_date,
        required=False,
        help='Date from which to start pulling data.',
    )
    collect.add_argument(
        '-m',
        '--max-days',
        type=int,
        required=False,
        help='Max days of data to pull if start-date is not given.',
    )
    collect.add_argument(
        '-d',
        '--dry-run',
        action='store_true',
        help='Do not run the actual query, only simulate it.',
    )
    collect.add_argument(
        '-f',
        '--force',
        action='store_true',
        help='Force the download even if the data already exists or there is a gap',
    )
    collect.add_argument(
        '-M',
        '--add-metrics',
        action='store_true',
        help='Compute the aggregation metrics and create the corresponding spreadsheets.',
    )

    return parser


def main():
    """Run the Download Analytics CLI."""
    parser = _get_parser()
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    _env_setup(args.logfile, args.verbose)
    args.action(args)


if __name__ == '__main__':
    main()
