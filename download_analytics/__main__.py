"""Github Analytics CLI."""

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
        import_projects = import_config['projects']

        import_config.update(config)
        config = import_config

        config_projects = config['projects']
        for spreadsheet, projects in config_projects.items():
            if not projects:
                config_projects[spreadsheet] = import_projects[spreadsheet]

    return config


def _collect(args, parser):
    config = _load_config(args.config_file)
    config_projects = config['projects']

    projects = {}
    if args.projects:
        if not args.spreadsheets:
            parser.error('If projects are given, spreadsheet name must be provided.')
        elif len(args.spreadsheets) > 1:
            parser.error('If projects are given, only one spreadsheet name must be provided.')

        projects = {
            args.spreadsheets[0]: args.projects
        }

    elif not args.projects:
        projects = config_projects

    else:
        for spreadsheet in args.projects:
            if spreadsheet not in config_projects:
                LOGGER.error('Unknown projects spreadsheet %s', spreadsheet)
                return

            projects[spreadsheet] = config_projects[spreadsheet]

    output_path = args.output_path or config.get('output-path', '.')
    max_days = args.max_days or config.get('max-days')

    collect_downloads(
        projects=projects,
        start_date=args.start_date,
        output_path=output_path,
        max_days=max_days,
        credentials_file=args.authentication_credentials,
        dry_run=args.dry_run,
        force=args.force,
    )


def valid_date(arg):
    try:
        return datetime.strptime(arg, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f'Invalid date: {arg}')


def _get_parser():
    # Logging
    logging_args = argparse.ArgumentParser(add_help=False)
    logging_args.add_argument('-v', '--verbose', action='count', default=1)
    logging_args.add_argument('-l', '--logfile')

    parser = argparse.ArgumentParser(
        prog='download-analytics',
        description='Download Analytics Command Line Interface',
        parents=[logging_args]
    )
    parser.set_defaults(action=None)
    action = parser.add_subparsers(title='action')
    action.required = True

    # collect
    collect = action.add_parser('collect', help='Collect downloads data.', parents=[logging_args])
    collect.set_defaults(action=_collect)

    collect.add_argument(
        '-o', '--output-path', type=str, required=False,
        help='Output path. ')
    collect.add_argument(
        '-a', '--authentication-credentials', type=str, required=False,
        help='Path to the credentials file to use.')
    collect.add_argument(
        '-s', '--spreadsheets', type=str, nargs='*',
        help='Spreadsheets to collect. Defaults to ALL the configuried ones if not given.')
    collect.add_argument(
        '-c', '--config-file', type=str, default='config.yaml',
        help='Path to the configuration file.')
    collect.add_argument(
        '-p', '--projects', nargs='*',
        help='List of projects to collect. If not given use the configured ones.')
    collect.add_argument(
        '-S', '--start-date', type=valid_date, required=False,
        help='Date from which to start pulling data.')
    collect.add_argument(
        '-m', '--max-days', type=int, required=False,
        help='Max days of data to pull of start-date is not given.')
    collect.add_argument(
        '-d', '--dry-run', action='store_true',
        help='Do not run the actual query.')
    collect.add_argument(
        '-f', '--force', action='store_true',
        help='Force the download even if the data already exists or there is a gap')

    return parser


def main():
    """Run the Github Analytics CLI."""
    parser = _get_parser()
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    _env_setup(args.logfile, args.verbose)
    args.action(args, parser)


if __name__ == '__main__':
    main()
