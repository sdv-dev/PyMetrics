"""Functions to get GitHub downloads from GitHub."""

import logging
import os
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from tqdm import tqdm

from pymetrics.github import GithubClient
from pymetrics.output import append_row, create_csv, get_path, load_csv
from pymetrics.time_utils import drop_duplicates_by_date

LOGGER = logging.getLogger(__name__)
dir_path = os.path.dirname(os.path.realpath(__file__))
TIME_COLUMN = 'timestamp'

GITHUB_DOWNLOAD_COUNT_FILENAME = 'github_download_counts.csv'


def get_previous_github_downloads(output_folder, dry_run=False):
    csv_path = get_path(output_folder, GITHUB_DOWNLOAD_COUNT_FILENAME)
    read_csv_kwargs = {
        'parse_dates': [
            TIME_COLUMN,
            'created_at',
        ],
        'dtype': {
            'ecosystem_name': pd.CategoricalDtype(),
            'org_repo': pd.CategoricalDtype(),
            'tag_name': pd.CategoricalDtype(),
            'prerelease': pd.BooleanDtype(),
            'download_count': pd.Int64Dtype(),
        },
    }
    data = load_csv(csv_path, read_csv_kwargs=read_csv_kwargs)
    return data


def collect_github_downloads(
    projects: dict[str, list[str]], output_folder: str, dry_run: bool = False, verbose: bool = False
):
    overall_df = get_previous_github_downloads(output_folder=output_folder)
    # overall_df = pd.DataFrame(
    #     columns=[
    #         TIME_COLUMN,
    #         'created_at',
    #         'ecosystem_name',
    #         'org_repo',
    #         'tag_name',
    #         'prerelease',
    #         'download_count',
    #     ]
    # )

    gh_client = GithubClient()
    download_counts = defaultdict(int)

    for ecosystem_name, repositories in tqdm(projects.items(), position=2, desc='Overall'):
        for org_repo in tqdm(repositories, position=1, desc=f'For Ecosystem: {ecosystem_name}'):
            pages_remain = True
            page = 1
            per_page = 100
            download_counts[org_repo] = 0

            github_org = org_repo.split('/')[0]
            repo = org_repo.split('/')[1]

            while pages_remain is True:
                response = gh_client.get(
                    github_org,
                    repo,
                    endpoint='releases',
                    query_params={'per_page': per_page, 'page': page},
                )
                release_data = response.json()
                link_header = response.headers.get('link')

                if response.status_code == 404:
                    LOGGER.debug(f'Skipping: {org_repo} because org/repo does not exist')
                    pages_remain = False
                    break

                # Get download count
                for release_info in tqdm(
                    release_data, position=0, desc=f'For {repo} releases, page: {page}'
                ):
                    release_id = release_info.get('id')
                    tag_name = release_info.get('tag_name')
                    prerelease = release_info.get('prerelease')
                    created_at = release_info.get('created_at')
                    endpoint = f'releases/{release_id}'
                    timestamp = datetime.now(ZoneInfo('UTC'))

                    response = gh_client.get(github_org, repo, endpoint=endpoint)
                    data = response.json()
                    assets = data.get('assets')
                    tag_row = {
                        'ecosystem_name': [ecosystem_name],
                        'org_repo': [org_repo],
                        'timestamp': [timestamp],
                        'tag_name': [tag_name],
                        'prerelease': [prerelease],
                        'created_at': [created_at],
                        'download_count': 0,
                    }
                    if assets and len(assets) > 0:
                        for asset in assets:
                            tag_row['download_count'] += asset.get('download_count', 0)

                    overall_df = append_row(overall_df, tag_row)

                # Check pagination
                if link_header and 'rel="next"' in link_header:
                    page += 1
                else:
                    break
    overall_df = drop_duplicates_by_date(
        overall_df,
        time_column=TIME_COLUMN,
        group_by_columns=['ecosystem_name', 'org_repo', 'tag_name'],
    )
    overall_df.to_csv('github_download_counts.csv', index=False)

    if not dry_run:
        gfolder_path = f'{output_folder}/{GITHUB_DOWNLOAD_COUNT_FILENAME}'
        create_csv(output_path=gfolder_path, data=overall_df)
