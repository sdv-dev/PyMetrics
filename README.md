<div align="center">
<br/>
<p align="center">
    <i>An open source project by Engineering at <a href="https://datacebo.com">DataCebo</a>.</i>
</p>


[![Dev Status](https://img.shields.io/badge/Dev%20Status-5%20--%20Production%2fStable-green)](https://pypi.org/search/?c=Development+Status+%3A%3A+5+-+Production%2FStable)
[![Unit Tests](https://github.com/datacebo/PyMetrics/actions/workflows/unit.yaml/badge.svg)](https://github.com/datacebo/PyMetrics/actions/workflows/unit.yaml?query=branch%3Amain)
[![Slack](https://img.shields.io/badge/Slack-Join%20now!-36C5F0?logo=slack)](https://bit.ly/sdv-slack-invite)


  <div align="center">
    <a href="https://datacebo.com">
      <picture>
          <img align="center" width=40% src="https://github.com/sdv-dev/PyMetrics/blob/main/docs/images/datacebo-logo.png"></img>
      </picture>
    </a>
  </div>
</div>

<br/>

<div align="left">
  <picture>
      <img align="center" width=25% src="https://github.com/sdv-dev/PyMetrics/blob/main/docs/images/pymetrics-logo.png"></img>
  </picture>
</div>

---

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

* [GitHub Releases](https://docs.github.com/en/rest/releases): Information about the project downloads from GitHub release assets.
  See this [GitHub API](https://docs.github.com/en/rest/releases/releases?apiVersion=2022-11-28#get-a-release).

# Install
Install pymetrics using pip (or uv):
```shell
pip install git+ssh://git@github.com/sdv-dev/pymetrics
```

## Local Usage
Collect metrics from PyPI by running `pymetrics` on your computer. You need to provide the following:

1. BigQuery Credentials. In order to get PyPI download data, you need to execute queries on Google BigQuery.
  Therefore, you will need an authentication JSON file, which must be provided to you by a privileged admin.
  Once you have this JSON file, export the contents of the credentials file into a
  `BIGQUERY_CREDENTIALS` environment variable.
2. A list of PyPI projects for which to collect the download metrics, defined in a YAML file.
   See [config.yaml](./config.yaml) for an example.
3. Optional. A set of Google Drive Credentials can be provided in the format required by `PyDrive`. The
   credentials can be passed via the `PYDRIVE_CREDENTIALS` environment variable.
   - See [instructions from PyDrive](https://pythonhosted.org/PyDrive/quickstart.html).

You can run pymetrics with the following CLI command:

```shell
pymetrics collect-pypi --max-days 30 --add-metrics --output-folder {OUTPUT_FOLDER}
```

## Workflows

### Daily Collection
On a daily basis, this workflow collects download data from PyPI and Anaconda. The data is then published in CSV format (`pypi.csv`). In addition, it computes metrics for the PyPI downloads (see [#Aggregation Metrics](#aggregation-metrics))

### Daily Summarization

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

## PyPI Data
PyMetrics collects download information from PyPI by querying the [public PyPI download statistics dataset on BigQuery](https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=pypi&page=dataset). The following data fields are captured for each download event:

**Temporal & Geographic Data:**
* `timestamp`: The timestamp at which the download happened
* `country_code`: The 2-letter country code

**Package Information:**
* `project`: The name of the PyPI project (library) that is being downloaded
* `version`: The downloaded version
* `type`: The type of file that was downloaded (source or wheel)

**Installation Environment:**
* `installer_name`: The installer used for the download, like `pip` or `bandersnatch` or `uv`
* `implementation_name`: The name of the Python implementation, such as `cpython`
* `implementation_version`: The Python version
* `ci`: A boolean flag indicating whether the download originated from a CI system (True, False, or null). This is determined by checking for specific environment variables set by CI platforms such as Azure Pipelines (`BUILD_BUILDID`), Jenkins (`BUILD_ID`), or general CI indicators (`CI`, `PIP_IS_CI`)

**System Information:**
* `distro_name`: Name of the Linux or Mac distribution (empty if Windows)
* `distro_version`: Distribution version (empty for Windows)
* `system_name`: Type of OS, like Linux, Darwin (for Mac), or Windows
* `system_release`: OS version in case of Windows, kernel version in case of Unix
* `cpu`: CPU architecture used

## Aggregation Metrics

If the `--add-metrics` option is passed to `pymetrics`, a spreadsheet with aggregation
metrics will be created alongside the raw PyPI downloads CSV file for each individual project.

The aggregation metrics spreasheets contain the following tabs:

* **By Month:** Number of downloads per month and increase in the number of downloads from month to month.
* **By Version:** Absolute and relative number of downloads per version.
* **By Country Code:** Absolute and relative number of downloads per Country.
* **By Python Version:** Absolute and relative number of downloads per minor Python Version (X.Y, like 3.8).
* **By Full Python Version:** Absolute and relative number of downloads per Python Version, including
  the patch number (X.Y.Z, like 3.8.1).
* **By Installer Name:** Absolute and relative number of downloads per Installer (e.g. pip)
* **By Distro Name:** Absolute and relative number of downloads per Distribution Name (e.g. Ubuntu)
* **By Distro Name:** Absolute and relative number of downloads per Distribution Name AND Version (e.g. Ubuntu 20.04)
* **By Distro Kernel:** Absolute and relative number of downloads per Distribution Name, Version AND Kernel (e.g. Ubuntu 18.04 - 5.4.104+)
* **By OS Type:** Absolute and relative number of downloads per OS Type (e.g. Linux)
* **By Cpu:** Absolute and relative number of downloads per CPU Version (e.g. AMD64)
* **By CI**: Absolute and relative number of downloads by CI status (automated vs. manual installations)
* **By Month and Version:** Absolute number of downloads per month and version.
* **By Month and Python Version:** Absolute number of downloads per month and Python version.
* **By Month and Country Code:** Absolute number of downloads per month and country.
* **By Month and Installer Name:** Absolute number of downloads per month and Installer.
* **By Prerelease**: Absolute and relative number of downloads for pre-release versions (alpha, beta, release candidate, and development versions).
* **By Postrelease**: Absolute and relative number of downloads for post-release versions.
* **By Devrelease**: Absolute and relative number of downloads for development release versions.

## Known Issues
1. The conda package download data for Anaconda does not match the download count shown on the website. This is due to missing download data in the conda package download data. See this: https://github.com/anaconda/anaconda-package-data/issues/45
