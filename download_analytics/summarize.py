"""Functionality to summarize download data."""

import logging
import os

import pandas as pd

from download_analytics.constants import pre_bsl_versions
from download_analytics.output import create_spreadsheet, get_path, load_csv
from download_analytics.time_utils import get_current_year, get_min_max_dt_in_year

TOTAL_COLUMN_NAME = 'Total Since Beginning'
ECOSYSTEM_COLUMN_NAME = 'Ecosystem'
BREAKDOWN_COLUMN_NAME = 'Library'
BSL_COLUMN_NAME = 'Type'
SHEET_NAMES = [
    'all',
    'vendor-mapping',
    'SDV',
    'PreBSL-vs-BSL',
]
OUTPUT_FILENAME = 'Downloads_Summary'

dir_path = os.path.dirname(os.path.realpath(__file__))

LOGGER = logging.getLogger(__name__)


def _calculate_projects_count(
    downloads,
    projects,
    max_datetime=None,
    min_datetime=None,
    versions=None,
    opposite_versions=False,
):
    if isinstance(projects, str):
        projects = (projects,)

    project_downloads = downloads[downloads['project'].isin(set(projects))]
    if versions and len(versions) > 0:
        if opposite_versions is False:
            project_downloads = project_downloads[project_downloads['version'].isin(set(versions))]
        else:
            project_downloads = project_downloads[~project_downloads['version'].isin(set(versions))]

    if max_datetime:
        project_downloads = project_downloads[project_downloads['timestamp'] <= max_datetime]
    if min_datetime:
        project_downloads = project_downloads[project_downloads['timestamp'] >= min_datetime]

    return len(project_downloads)


def _create_counts_list(
    base_count, dependency_projects, dep_to_count, parent_projects, parent_to_count
):
    counts = [base_count]
    for dep in dependency_projects:
        counts.append(dep_to_count[dep])
    for lib in parent_projects:
        counts.append(parent_to_count[lib])
    return counts


def _sum_counts(base_count, dep_to_count, parent_to_count):
    # Do not adjust counts, as _calculate_adjusted_count already did that
    return base_count + sum(parent_to_count.values()) + sum(dep_to_count.values())


def append_row(df, row):
    """Append a dictionary as a row to a DataFrame."""
    return pd.concat([df, pd.DataFrame(data=row)], ignore_index=True)


def get_downloads(input_file, output_folder, dry_run):
    """Read pypi.csv and return a DataFrame of the downloads."""
    if input_file:
        downloads = load_csv(input_file, dry_run=dry_run)
    else:
        csv_path = get_path(output_folder, 'pypi.csv')
        downloads = load_csv(csv_path, dry_run=dry_run)
    return downloads


def _ecosystem_count_by_year(downloads, base_project, dependency_projects, parent_projects):
    row_info = {ECOSYSTEM_COLUMN_NAME: [base_project]}
    breakdown_info = {}

    for year in range(2021, get_current_year() + 1):
        min_datetime, max_datetime = get_min_max_dt_in_year(year)
        base_count, dep_to_count, parent_to_count = _calculate_adjusted_count(
            downloads,
            base_project=base_project,
            dependency_projects=dependency_projects,
            parent_projects=parent_projects,
            min_datetime=min_datetime,
            max_datetime=max_datetime,
        )
        row_info[year] = _sum_counts(
            base_count=base_count, dep_to_count=dep_to_count, parent_to_count=parent_to_count
        )
        breakdown_projects = [base_project] + dependency_projects + parent_projects
        breakdown_info[BREAKDOWN_COLUMN_NAME] = breakdown_projects
        counts = _create_counts_list(
            base_count=base_count,
            dependency_projects=dependency_projects,
            dep_to_count=dep_to_count,
            parent_projects=parent_projects,
            parent_to_count=parent_to_count,
        )
        breakdown_info[year] = counts
    return row_info, breakdown_info


def _version_count_by_year(
    downloads,
    base_project,
    dependency_projects,
    parent_projects,
    type_,
    project_to_versions,
    opposite_versions=False,
):
    row_info = {BSL_COLUMN_NAME: [type_]}
    base_count, dep_to_count, parent_to_count = _calculate_adjusted_count(
        downloads,
        base_project=base_project,
        dependency_projects=dependency_projects,
        parent_projects=parent_projects,
        project_to_versions=project_to_versions,
        opposite_versions=opposite_versions,
    )
    row_info[TOTAL_COLUMN_NAME] = [
        _sum_counts(
            base_count=base_count, dep_to_count=dep_to_count, parent_to_count=parent_to_count
        )
    ]

    for year in range(2021, get_current_year() + 1):
        min_datetime, max_datetime = get_min_max_dt_in_year(year)
        base_count, dep_to_count, parent_to_count = _calculate_adjusted_count(
            downloads,
            base_project=base_project,
            dependency_projects=dependency_projects,
            parent_projects=parent_projects,
            project_to_versions=project_to_versions,
            min_datetime=min_datetime,
            max_datetime=max_datetime,
            opposite_versions=opposite_versions,
        )
        row_info[year] = [
            _sum_counts(
                base_count=base_count, dep_to_count=dep_to_count, parent_to_count=parent_to_count
            )
        ]
    return row_info


def summarize_downloads(
    projects,
    vendors,
    output_folder,
    input_file=None,
    dry_run=False,
    verbose=False,
):
    """Summarize download data from pypi.csv.

    Args:
        projects (dict[str, str | list[str]]):
            List of projects/ecosysems to summarize. Each project must have ecosystem (str).
            If it is an ecosystem and download counts needs to be adjusted it must have:
                - base_project (str): This is the base project for the ecosystem.
                - dependency_projects (list[str]): These are direct dependencies of the base project
                    and maintained by the same org.
                    The downloads counts are subtracted from the base project, since they are
                    direct dependencies.
                - parent_projects (list[str]): These are parent projects maintained by the same org.
                    These parent projects have a core dependency on the base project.
                    Their base project download count is subtracted from each parent parent.
            If the downloads counts should be simply added together, then the following is required:
                - projects (list[list]): The list of projects to add.

        vendors (dict[str, str | list[str]]):
            The vendors and the projects owned by the Vendors.
            For each vendor, the following must be defined:
                - ecosystem (str): The user facing name.
                - name (str): The actual name of the vendor.
                - projects (list[str]): The projects owned by the vendor.
                    The downloads counts are summed.

        output_folder (str):
            Folder in which project downloads will be stored.
            It can be passed as a local folder or as a Google Drive path in the format
            `gdrive://{folder_id}`.

    """
    downloads = get_downloads(input_file, output_folder, dry_run)

    vendor_df = pd.DataFrame.from_records(vendors)
    all_df = _create_all_df()
    breakdown_df = _create_breakdown_df()
    bsl_vs_pre_bsl_df = _create_bsl_vs_prebsl_df()
    projects.extend(vendors)

    for project_info in projects:
        ecosystem_name = project_info['ecosystem']

        base_project = project_info.get('base_project')
        dependency_projects = project_info.get('dependency_projects')
        parent_projects = project_info.get('parent_projects')
        calculate_breakdown = project_info.get('calculate_breakdown', False)

        projects = project_info.get('projects')
        row_info = {ECOSYSTEM_COLUMN_NAME: [ecosystem_name]}
        if base_project:
            row_info, breakdown_info = _ecosystem_count_by_year(
                downloads=downloads,
                base_project=base_project,
                dependency_projects=dependency_projects,
                parent_projects=parent_projects,
            )
            base_count, dep_to_count, parent_to_count = _calculate_adjusted_count(
                downloads,
                base_project=base_project,
                dependency_projects=dependency_projects,
                parent_projects=parent_projects,
            )
            row_info[TOTAL_COLUMN_NAME] = _sum_counts(
                base_count=base_count, dep_to_count=dep_to_count, parent_to_count=parent_to_count
            )
            breakdown_info[TOTAL_COLUMN_NAME] = _create_counts_list(
                base_count=base_count,
                dependency_projects=dependency_projects,
                dep_to_count=dep_to_count,
                parent_projects=parent_projects,
                parent_to_count=parent_to_count,
            )

            all_df = append_row(all_df, row_info)
            if calculate_breakdown:
                breakdown_df = append_row(breakdown_df, breakdown_info)
        elif projects:
            for year in range(2021, get_current_year() + 1):
                min_datetime, max_datetime = get_min_max_dt_in_year(year)
                row_info[year] = _calculate_projects_count(
                    downloads,
                    projects=projects,
                    min_datetime=min_datetime,
                    max_datetime=max_datetime,
                )

            row_info[TOTAL_COLUMN_NAME] = _calculate_projects_count(downloads, projects=projects)
            all_df = append_row(all_df, row_info)

        if ecosystem_name.lower() == 'sdv':
            version_row = _version_count_by_year(
                downloads=downloads,
                base_project=base_project,
                dependency_projects=dependency_projects,
                parent_projects=parent_projects,
                type_='Pre-BSL',
                project_to_versions=pre_bsl_versions,
                opposite_versions=False,
            )
            bsl_vs_pre_bsl_df = append_row(bsl_vs_pre_bsl_df, version_row)
            version_row = _version_count_by_year(
                downloads=downloads,
                base_project=base_project,
                dependency_projects=dependency_projects,
                parent_projects=parent_projects,
                type_='BSL',
                project_to_versions=pre_bsl_versions,
                opposite_versions=True,
            )
            bsl_vs_pre_bsl_df = append_row(bsl_vs_pre_bsl_df, version_row)
    vendor_df = vendor_df.rename(columns={vendor_df.columns[0]: ECOSYSTEM_COLUMN_NAME})
    sheets = {
        SHEET_NAMES[0]: all_df,
        SHEET_NAMES[1]: vendor_df,
        SHEET_NAMES[2]: breakdown_df,
        SHEET_NAMES[3]: bsl_vs_pre_bsl_df,
    }
    if verbose:
        for sheet_name, df in sheets.items():
            LOGGER.info(f'Sheet Name: {sheet_name}')
            LOGGER.info(df)
    if not dry_run:
        # Write to Google Drive/Output folder
        output_path = os.path.join(output_folder, OUTPUT_FILENAME)
        create_spreadsheet(output_path=output_path, sheets=sheets)

        # Write to local directory
        output_path = os.path.join(dir_path, OUTPUT_FILENAME)
        create_spreadsheet(output_path=output_path, sheets=sheets)


def _create_all_df():
    columns = [ECOSYSTEM_COLUMN_NAME, TOTAL_COLUMN_NAME]
    for year in range(2021, get_current_year() + 1):
        columns.append(year)
    return pd.DataFrame(columns=columns)


def _create_breakdown_df():
    breakdown_df = _create_all_df()
    return breakdown_df.rename(columns={ECOSYSTEM_COLUMN_NAME: BREAKDOWN_COLUMN_NAME})


def _create_bsl_vs_prebsl_df():
    sdv_df = _create_all_df()
    return sdv_df.rename(columns={ECOSYSTEM_COLUMN_NAME: BSL_COLUMN_NAME})


def _calculate_adjusted_count(
    downloads,
    base_project,
    dependency_projects,
    parent_projects,
    max_datetime=None,
    min_datetime=None,
    project_to_versions=None,
    opposite_versions=False,
):
    dependency_to_count = {}
    parent_to_count = {}
    if not project_to_versions:
        project_to_versions = {}

    for parent_project in parent_projects:
        project_count = _calculate_projects_count(
            downloads,
            projects=[parent_project],
            max_datetime=max_datetime,
            min_datetime=min_datetime,
            versions=project_to_versions.get(parent_project),
            opposite_versions=opposite_versions,
        )
        parent_to_count[parent_project] = project_count

    base_count = _calculate_projects_count(
        downloads,
        projects=[base_project],
        max_datetime=max_datetime,
        min_datetime=min_datetime,
        versions=project_to_versions.get(base_project),
        opposite_versions=opposite_versions,
    )

    for dependency_project in dependency_projects:
        if dependency_project == base_project:
            raise ValueError('Base project cannot be in dependency project.')
        dep_count = _calculate_projects_count(
            downloads,
            projects=[dependency_project],
            max_datetime=max_datetime,
            min_datetime=min_datetime,
            versions=project_to_versions.get(dependency_project),
            opposite_versions=opposite_versions,
        )
        dependency_to_count[dependency_project] = dep_count

    # Adjust base project to account for parent projects
    for _, project_count in parent_to_count.items():
        base_count -= project_count

    # Adjust dependency project to account for base project
    for dependency_project in dependency_projects:
        adjusted_dep_count = dependency_to_count[dependency_project]

        adjusted_dep_count = adjusted_dep_count - base_count
        adjusted_dep_count = max(0, adjusted_dep_count)
        dependency_to_count[dependency_project] = adjusted_dep_count

    return base_count, dependency_to_count, parent_to_count
