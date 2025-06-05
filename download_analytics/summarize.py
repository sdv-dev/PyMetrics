
import os

import pandas as pd

from download_analytics.constants import pre_bsl_versions
from download_analytics.output import create_spreadsheet, get_path, load_csv
from download_analytics.time_utils import get_current_year, get_min_max_dt_in_year

TOTAL_COLUMN_NAME = "Total Since Beginning"
ECOSYSTEM_COLUMN_NAME = "Ecosystem"
BREAKDOWN_COLUMN_NAME = "Library"
BSL_COLUMN_NAME = "Type"
SHEET_NAMES = [
    'all',
    'vendor-mapping',
    'SDV',
    'PreBSL-vs-BSL',
]
OUTPUT_FILENAME = "Downloads | Summary"


def calculate_projects_count(downloads, projects,
                             max_datetime=None, min_datetime=None,
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


def _create_counts_list(base_count, dependency_projects, dep_to_count, extra_projects, lib_to_count):
    counts = [base_count]
    for dep in dependency_projects:
        counts.append(dep_to_count[dep])
    for lib in extra_projects:
        counts.append(lib_to_count[lib])
    return counts


def _sum_counts(base_count, dep_to_count, lib_to_count):
    return base_count + sum(dep_to_count.values()) + sum(lib_to_count.values())


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


def _ecosystem_count_by_year(downloads,
                            base_project,
                            dependency_projects,
                            extra_projects):
    row_info = {
        ECOSYSTEM_COLUMN_NAME: [base_project]
    }
    breakdown_info = {}

    for year in range(2021, get_current_year() + 1):
        min_datetime, max_datetime = get_min_max_dt_in_year(year)
        base_count, dep_to_count, lib_to_count = _calculate_adjusted_count(downloads,
                                                    base_project=base_project,
                                                    dependency_projects=dependency_projects,
                                                    extra_projects=extra_projects,
                                                    min_datetime=min_datetime,
                                                    max_datetime=max_datetime)
        row_info[year] = _sum_counts(base_count=base_count,
                                    dep_to_count=dep_to_count,
                                    lib_to_count=lib_to_count)
        breakdown_info[BREAKDOWN_COLUMN_NAME] = [base_project] + dependency_projects + extra_projects
        counts = _create_counts_list(base_count=base_count,
                                    dependency_projects=dependency_projects,
                                    dep_to_count=dep_to_count,
                                    extra_projects=extra_projects,
                                    lib_to_count=lib_to_count)
        breakdown_info[year] = counts
    return row_info, breakdown_info


def _version_count_by_year(downloads,
                           base_project,
                           dependency_projects,
                           extra_projects,
                           type_,
                           project_to_versions,
                           opposite_versions=False):
    row_info = {
        BSL_COLUMN_NAME: [type_]
    }
    base_count, dep_to_count, lib_to_count = _calculate_adjusted_count(downloads,
                                                                        base_project=base_project,
                                                                        dependency_projects=dependency_projects,
                                                                        extra_projects=extra_projects,
                                                                        project_to_versions=project_to_versions,
                                                                        opposite_versions=opposite_versions,)
    row_info[TOTAL_COLUMN_NAME] = [_sum_counts(base_count=base_count, dep_to_count=dep_to_count, lib_to_count=lib_to_count)]

    for year in range(2021, get_current_year() + 1):
        min_datetime, max_datetime = get_min_max_dt_in_year(year)
        base_count, dep_to_count, lib_to_count = _calculate_adjusted_count(downloads,
                                                                           base_project=base_project,
                                                                           dependency_projects=dependency_projects,
                                                                           extra_projects=extra_projects,
                                                                           project_to_versions=project_to_versions,
                                                                           min_datetime=min_datetime,
                                                                           max_datetime=max_datetime,
                                                                           opposite_versions=opposite_versions)
        row_info[year] = [_sum_counts(base_count=base_count, dep_to_count=dep_to_count, lib_to_count=lib_to_count)]
    return row_info


def summarize_downloads(projects, vendors,
                        output_folder,
                        input_file=None,
                        dry_run=False):
    downloads = get_downloads(input_file,
                              output_folder,
                              dry_run)

    vendor_df = pd.DataFrame.from_records(vendors)
    all_df = _create_all_df()
    breakdown_df = _create_breakdown_df()
    bsl_vs_pre_bsl_df = _create_bsl_vs_prebsl_df()
    projects.extend(vendors)

    for project_info in projects:
        ecosystem_name = project_info["ecosystem_name"]

        base_project = project_info.get('base_project')
        dependency_projects = project_info.get('dependency_projects')
        extra_projects = project_info.get('extra_projects')
        calculate_breakdown = project_info.get('calculate_breakdown', False)

        vendor_name = project_info.get("name", None)

        projects = project_info.get("projects")
        row_info = {
            ECOSYSTEM_COLUMN_NAME: [ecosystem_name]
        }
        if base_project:
            row_info, breakdown_info = _ecosystem_count_by_year(downloads=downloads,
                                                               base_project=base_project,
                                                               dependency_projects=dependency_projects,
                                                               extra_projects=extra_projects)
            base_count, dep_to_count, lib_to_count = _calculate_adjusted_count(downloads,
                                                                               base_project=base_project,
                                                                               dependency_projects=dependency_projects,
                                                                               extra_projects=extra_projects)
            row_info[TOTAL_COLUMN_NAME] = _sum_counts(base_count=base_count,
                                                      dep_to_count=dep_to_count,
                                                      lib_to_count=lib_to_count)
            breakdown_info[TOTAL_COLUMN_NAME] = _create_counts_list(base_count=base_count,
                                                                dependency_projects=dependency_projects,
                                                                dep_to_count=dep_to_count,
                                                                extra_projects=extra_projects,
                                                                lib_to_count=lib_to_count)

            all_df = append_row(all_df, row_info)
            if calculate_breakdown:
                breakdown_df = append_row(breakdown_df, breakdown_info)
        elif projects:
            for year in range(2021, get_current_year() + 1):
                min_datetime, max_datetime = get_min_max_dt_in_year(year)
                row_info[year] = calculate_projects_count(downloads,
                                                           projects=projects,
                                                           min_datetime=min_datetime,
                                                           max_datetime=max_datetime)

            row_info[TOTAL_COLUMN_NAME] = calculate_projects_count(downloads,
                                                                   projects=projects)
            all_df = append_row(all_df, row_info)

        if ecosystem_name.lower() == "sdv":
            version_row = _version_count_by_year(
                downloads=downloads,
                base_project=base_project,
                dependency_projects=dependency_projects,
                extra_projects=extra_projects,
                type_='Pre-BSL',
                project_to_versions=pre_bsl_versions,
                opposite_versions=False,
            )
            bsl_vs_pre_bsl_df = append_row(bsl_vs_pre_bsl_df, version_row)
            version_row = _version_count_by_year(
                downloads=downloads,
                base_project=base_project,
                dependency_projects=dependency_projects,
                extra_projects=extra_projects,
                type_='BSL',
                project_to_versions=pre_bsl_versions,
                opposite_versions=True,
            )
            bsl_vs_pre_bsl_df = append_row(bsl_vs_pre_bsl_df, version_row)
    sheets = {
        SHEET_NAMES[0]: all_df,
        SHEET_NAMES[1]: vendor_df,
        SHEET_NAMES[2]: breakdown_df,
        SHEET_NAMES[3]: bsl_vs_pre_bsl_df,
    }
    output_path = os.path.join(output_folder, OUTPUT_FILENAME)
    create_spreadsheet(output_path=output_path,
                       sheets=sheets,
                       add_commas=True)


def _create_all_df():
    columns = [ECOSYSTEM_COLUMN_NAME, TOTAL_COLUMN_NAME]
    for year in range(2021, get_current_year() + 1):
        columns.append(year)
    return pd.DataFrame(columns=columns)


def _create_breakdown_df():
    breakdown_df = _create_all_df()
    return breakdown_df.rename(columns={
        ECOSYSTEM_COLUMN_NAME: BREAKDOWN_COLUMN_NAME
    })


def _create_bsl_vs_prebsl_df():
    sdv_df = _create_all_df()
    return sdv_df.rename(columns={
        ECOSYSTEM_COLUMN_NAME: BSL_COLUMN_NAME
    })


def _calculate_adjusted_count(downloads,
                             base_project,
                             dependency_projects,
                             extra_projects,
                             max_datetime=None,
                             min_datetime=None,
                             project_to_versions=None,
                             opposite_versions=False):
    dependency_to_count = {}
    extra_to_count = {}
    if not project_to_versions:
        project_to_versions = {}
    base_count = calculate_projects_count(
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
        dep_count = calculate_projects_count(
            downloads,
            projects=[dependency_project],
            max_datetime=max_datetime,
            min_datetime=min_datetime,
            versions=project_to_versions.get(dependency_project),
            opposite_versions=opposite_versions,
        )
        dep_count = dep_count - base_count
        dep_count = max(0, dep_count)
        dependency_to_count[dependency_project] = dep_count

    for extra_project in extra_projects:
        project_count = calculate_projects_count(
            downloads,
            projects=[extra_project],
            max_datetime=max_datetime,
            min_datetime=min_datetime,
            versions=project_to_versions.get(extra_project),
            opposite_versions=opposite_versions,
        )
        extra_to_count[extra_project] = project_count

    return base_count, dependency_to_count, extra_to_count
