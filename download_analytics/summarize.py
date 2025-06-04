from datetime import datetime

import pandas as pd

from download_analytics.output import get_path, load_csv

TOTAL_COLUMN_NAME = "Total Since Beginning"
ECOSYSTEM_COLUMN_NAME = "Ecosystem"
SDV_COLUMN_NAME = "Library"


def calculate_projects_count(downloads, projects, max_datetime=None, min_datetime=None):
    if isinstance(projects, str):
        projects = (projects,)

    projects = downloads[downloads['project'].isin(set(projects))]

    if max_datetime:
        projects = projects[projects['timestamp'] <= max_datetime]
    if min_datetime:
        projects = projects[projects['timestamp'] >= min_datetime]
    return len(projects)


def get_current_year():
    return datetime.now().year


def get_first_datetime_in_year(year):
    min_date = datetime(year, day=1, month=1).date()
    return datetime.combine(min_date, datetime.min.time())


def get_last_datetime_in_year(year):
    max_date = datetime(year, day=31, month=12).date()
    return datetime.combine(max_date, datetime.max.time())


def summarize_downloads(projects, vendors,
                        output_folder,
                        input_file=None,
                        dry_run=False):

    if input_file:
        downloads = load_csv(input_file, dry_run=dry_run)
    else:
        csv_path = get_path(output_folder, 'pypi.csv')
        downloads = load_csv(csv_path, dry_run=dry_run)
    vendor_df = pd.DataFrame.from_records(vendors)

    all_df = create_all_df()
    sdv_df = create_sdv_df()
    projects.extend(vendors)

    for project_info in projects:
        name = project_info["name"]

        base_project = project_info.get('base_project')
        dependency_projects = project_info.get('dependency_projects')
        extra_projects = project_info.get('extra_projects')

        projects = project_info.get("projects")
        row_info = {
            ECOSYSTEM_COLUMN_NAME: [name]
        }

        if base_project:
            for year in range(2021, get_current_year() + 1):
                min_datetime = get_first_datetime_in_year(year)
                max_datetime = get_last_datetime_in_year(year)
                base_count, dep_to_count, lib_to_count = calculate_adjusted_count(downloads,
                                                           base_project=base_project,
                                                           dependency_projects=dependency_projects,
                                                           extra_projects=extra_projects,
                                                           min_datetime=min_datetime,
                                                           max_datetime=max_datetime)
                row_info[year] = base_count + sum(dep_to_count.values())
                row_info[year] += sum(lib_to_count.values())
                if base_project.lower() == "sdv":
                    type_ = [base_project] + dependency_projects + extra_projects
                    sdv_df["Library"] = type_
                    counts = [base_count]
                    for dep in dependency_projects:
                        counts.append(dep_to_count[dep])
                    for lib in extra_projects:
                        counts.append(lib_to_count[lib])
                    sdv_df[year] = counts

            base_count, dep_to_count, lib_to_count = calculate_adjusted_count(downloads,
                                                                   base_project=base_project,
                                                                   dependency_projects=dependency_projects,
                                                                   extra_projects=extra_projects)
            row_info[TOTAL_COLUMN_NAME] = base_count + sum(dep_to_count.values())
            row_info[TOTAL_COLUMN_NAME] += sum(lib_to_count.values())
            if base_project.lower() == "sdv":
                counts = [base_count]
                for dep in dependency_projects:
                    counts.append(dep_to_count[dep])
                for lib in extra_projects:
                    counts.append(lib_to_count[lib])
                sdv_df[TOTAL_COLUMN_NAME] = counts

        elif projects:
            for year in range(2021, get_current_year() + 1):
                min_datetime = get_first_datetime_in_year(year)
                max_datetime = get_last_datetime_in_year(year)
                row_info[year] = calculate_projects_count(downloads,
                                                           projects=projects,
                                                           min_datetime=min_datetime,
                                                           max_datetime=max_datetime)

            row_info[TOTAL_COLUMN_NAME] = calculate_projects_count(downloads,
                                                                   projects=projects)

        row = pd.DataFrame(data=row_info)
        all_df = pd.concat([all_df, row], ignore_index=True)

    print(all_df)
    print(vendor_df)
    print(sdv_df)


def create_all_df():
    columns = [ECOSYSTEM_COLUMN_NAME, TOTAL_COLUMN_NAME]
    for year in range(2021, get_current_year() + 1):
        columns.append(year)
    return pd.DataFrame(columns=columns)


def create_sdv_df():
    sdv_df = create_all_df()
    return sdv_df.rename(columns={
        ECOSYSTEM_COLUMN_NAME: SDV_COLUMN_NAME
    })


def calculate_adjusted_count(downloads,
                             base_project,
                             dependency_projects,
                             extra_projects,
                             max_datetime=None,
                             min_datetime=None):
    dependency_to_count = {}
    extra_to_count = {}
    base_count = calculate_projects_count(
        downloads,
        projects=[base_project],
        max_datetime=max_datetime,
        min_datetime=min_datetime
    )
    for dependency in dependency_projects:
        dep_count = calculate_projects_count(
            downloads,
            projects=[dependency],
            max_datetime=max_datetime,
            min_datetime=min_datetime,
        )
        dep_count = dep_count - base_count
        dep_count = max(0, dep_count)
        dependency_to_count[dependency] = dep_count

    for extra in extra_projects:
        project_count = calculate_projects_count(
            downloads,
            projects=[extra],
            max_datetime=max_datetime,
            min_datetime=min_datetime,
        )
        extra_to_count[extra] = project_count

    return base_count, dependency_to_count, extra_to_count
