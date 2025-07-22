<div align="center">
<br/>
<p align="center">
    <i>Originally developed for internal use by <a href="https://datacebo.com">DataCebo</a>, these projects are now available for the community.</i>
</p>

[![Dev Status](https://img.shields.io/badge/Dev%20Status-5%20--%20Production%2fStable-green)](https://pypi.org/search/?c=Development+Status+%3A%3A+5+-+Production%2FStable)
[![Unit Tests](https://github.com/datacebo/PyMetrics/actions/workflows/unit.yaml/badge.svg)](https://github.com/datacebo/PyMetrics/actions/workflows/unit.yaml?query=branch%3Amain)
[![Slack](https://img.shields.io/badge/Slack-Join%20now!-36C5F0?logo=slack)](https://bit.ly/sdv-slack-invite)

<div align="center">
  <a href="https://datacebo.com">
  <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://github.com/sdv-dev/SDV/blob/stable/docs/images/datacebo-logo-dark-mode.png">
      <img align="center" width=40% src="https://github.com/sdv-dev/SDV/blob/stable/docs/images/datacebo-logo.png"></img>
  </picture></a>
</div>
<br/>
</div>

# PyMetrics
The PyMetrics project allows you to extract download metrics for Python libraries published on [PyPI](https://pypi.org/) and [Anaconda](https://www.anaconda.com/).

The DataCebo team uses these scripts to report download counts for the libraries in the [SDV ecosystem](https://sdv.dev/) and other libraries.

## Overview
The PyMetrics project is a collection of scripts and tools to extract information
about OSS project downloads from different sources and to analyze them to produce user
engagement metrics.

### Data Sources
Currently, the download data is collected from the following distributions:
* [PyPI](https://pypi.org/): Information about the project downloads from [PyPI](https://pypi.org/)
  obtained from the public BigQuery dataset, equivalent to the information shown on
  [pepy.tech](https://pepy.tech), [ClickPy](https://clickpy.clickhouse.com/) or [pypistats](https://pypistats.org/).
  - More information about the BigQuery dataset can be found on the [official PyPI documentation](https://packaging.python.org/en/latest/guides/analyzing-pypi-package-downloads/).

* [Anaconda](https://www.anaconda.com/): Information about conda package downloads for default and select Anaconda channels.
  - The conda package download data is provided by Anaconda, Inc. It includes package download counts
    starting from January 2017. More information about this dataset can be found on the [official README.md](https://github.com/anaconda/anaconda-package-data/blob/master/README.md).
  - Additional conda package downloads are retrieved using the public API provided by Anaconda. This allows for the retrieval of the current number of downloads for each file served.
    - Anaconda API Endpoint: https://api.anaconda.org/package/{username}/{package_name}
      - Replace `{username}` with the Anaconda channel (`conda-forge`)
      - Replace `{package_name}` with the specific package (`sdv`) in the Anaconda channel
    - For each file returned by the API endpoint, the current number of downloads is saved. Over time, a historical download recording can be built.

### Future Data Sources
In the future, we may expand the source distributions to include:
* [GitHub Releases](https://github.com/): Information about the project downloads from GitHub releases.

## Workflows

### Daily Collection
On a daily basis, this workflow collects download data from PyPI and Anaconda. The data is then published in CSV format (`pypi.csv`). In addition, it computes metrics for the PyPI downloads (see below).

#### Metrics
This PyPI download metrics are computed along several dimensions:

- **By Month**: The number of downloads per month.
- **By Version**: The number of downloads per version of the software, as determined by the software maintainers.
- **By Python Version**: The number of downloads per minor Python version (eg. 3.8).
- **And more!**

### Daily Summarize

On a daily basis, this workflow summarizes the PyPI download data from `pypi.csv` and calculates downloads for libraries. The summarized data is published to a GitHub repo:
- [Downloads_Summary.xlsx](https://github.com/sdv-dev/sdv-dev.github.io/blob/gatsby-home/assets/Downloads_Summary.xlsx)

#### SDV Calculation
Installing the main SDV library also installs all the other libraries as dependencies. To calculate SDV downloads, we use an exclusive download methodology:

1. Get download counts for `sdgym` and `sdv`.
2. Adjust `sdv` downloads by subtracting `sdgym` downloads (since `sdgym` depends on `sdv`).
3. Get download counts for direct SDV dependencies: `rdt`, `copulas`, `ctgan`, `deepecho`, `sdmetrics`.
4. Adjust downloads for each dependency by subtracting the `sdv` download count (since `sdv` has a direct dependency).
5. Ensure no download count goes negative using `max(0, adjusted_count)` for each library.

This methodology prevents double-counting downloads while providing an accurate representation of SDV usage.

## Known Issues
1. The conda package download data for Anaconda does not match the download count shown on the website. This is due to missing download data in the conda package download data. See this: https://github.com/anaconda/anaconda-package-data/issues/45
