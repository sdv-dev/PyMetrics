"""Clients for making requests to Github APIs."""

import os

import requests


class BaseClient:
    """Base GitHub client."""

    def __init__(self):
        token = os.getenv('GH_ACCESS_TOKEN')
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }


class GithubClient(BaseClient):
    """Client for GitHub API."""

    def __init__(self):
        super().__init__()
        self.base_url = 'https://api.github.com/repos'

    def _construct_url(self, github_org: str, repo: str, resource: str, id: str | None = None):
        url = f'{self.base_url}/{github_org}/{repo}/{resource}'
        if id:
            url += f'/{id}'
        return url

    def get(
        self,
        github_org: str,
        repo: str,
        endpoint: str,
        query_params: dict | None = None,
        timeout: int | None = None,
    ):
        """Get a specific value of a resource from an endpoint in the GitHub API.

        Args:
            github_org (str):
                The name of the GitHub organization to search.
            repo (str):
                The name of the repository to search.
            endpoint (str):
                The endpoint for the resource. For example, issues/{issue_number}. This means we'd
                be making a request to https://api.github.com/repos/{github_org}/{repo}/issues/{issue_number}.
            query_params (dict):
                A dictionary mapping any query parameters to the desired value. Defaults to None.
            timeout (int):
                How long to wait before the request times out. Defaults to None.

        Returns:
            requests.models.Response
        """
        url = self._construct_url(github_org, repo, endpoint)
        return requests.get(url, headers=self.headers, params=query_params, timeout=timeout)

    def post(self, github_org: str, repo: str, endpoint: str, payload: dict):
        """Post to an endpooint in the GitHub API.

        Args:
            github_org (str):
                The name of the GitHub organization to search.
            repo (str):
                The name of the repository to search.
            endpoint (str):
                The endpoint for the resource. For example, issues. This means we'd be
                making a request to https://api.github.com/repos/{github_org}/{repo}/issues.
            payload (dict):
                The payload to post.

        Returns:
            requests.models.Response
        """
        url = self._construct_url(github_org, repo, endpoint)
        return requests.post(url, headers=self.headers, json=payload)
