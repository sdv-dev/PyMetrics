# Download Analytics

The Download Analytics project allows you to extract download metrics for Python libraries published on [PyPI](https://pypi.org/) and [Anaconda](https://www.anaconda.com/).

The DataCebo team uses these scripts to report download counts for the libraries in the [SDV ecosystem](https://sdv.dev/) and other libraries.

## Overview
The Download Analytics project is a collection of scripts and tools to extract information
about OSS project downloads from different sources and to analyze them to produce user
engagement metrics.

### Data Sources
Currently, the download data is collected from the following distributions:
* [PyPI](https://pypi.org/): Information about the project downloads from [PyPI](https://pypi.org/)
  obtained from the public BigQuery dataset, equivalent to the information shown on
  [pepy.tech](https://pepy.tech) and [ClickPy](https://clickpy.clickhouse.com/)
  - More information about the BigQuery dataset can be found on the [official PyPI documentation](https://packaging.python.org/en/latest/guides/analyzing-pypi-package-downloads/)

* [Anaconda](https://www.anaconda.com/): Information about conda package downloads for default and select Anaconda channels.
  - The conda package download data is provided by Anaconda, Inc. It includes package download counts
    starting from January 2017. More information about this dataset can be found on the [official README.md](https://github.com/anaconda/anaconda-package-data/blob/master/README.md).
  - Additional conda package downloads are retrieved using the public API provided by Anaconda. This allows for the retrieval of the current number of downloads for each file served.
    - Anaconda API Endpoint: https://api.anaconda.org/package/{username}/{package_name}
      - Replace `{username}` with the Anaconda channel (`conda-forge`)
      - Replace `{package_name}` with the specific package (`sdv`) in the Anaconda channel
    - For each file returned by the API endpoint, the current number of downloads is saved. Over time, a historical download recording can be built.
  - Both of these sources were used to track Anaconda downloads because the package data for Anaconda does not match the download count on the website. This is due to missing download data. See: https://github.com/anaconda/anaconda-package-data/issues/45

### Future Data Sources
In the future, we may expand the source distributions to include:
* [GitHub Releases](https://github.com/): Information about the project downloads from GitHub releases.

## Workflows

### Daily Collection
On a daily basis, this workflow collects download data from PyPI and Anaconda. The data is then published to Google Drive in CSV format (`pypi.csv`). In addition, it computes metrics for the PyPI downloads (see below).

#### Metrics
This PyPI download metrics are computed along several dimensions:

- **By Month**: The number of downloads per month.
- **By Version**: The number of downloads per version of the software, as determined by the software maintainers.
- **By Python Version**: The number of downloads per minor Python version (eg. 3.8).
- **By Full Python Version**: The number of downloads per full Python version (eg. 3.9.1).
- **And more!**

### Daily Summary

On a daily basis, this workflow summarizes the PyPI download data from `pypi.csv` and calculates downloads for libraries.

The summarized data is uploaded to a GitHub repo:
- [Downloads_Summary.xlsx](https://github.com/sdv-dev/sdv-dev.github.io/blob/gatsby-home/assets/Downloads_Summary.xlsx)

#### SDV Calculation
Installing the main SDV library also installs all the other libraries as dependencies. To calculate SDV downloads, we use an exclusive download methodology:

1. Get download counts for `sdgym` and `sdv`.
2. Adjust `sdv` downloads by subtracting `sdgym` downloads (since sdgym depends on sdv).
3. Get download counts for direct SDV dependencies: `rdt`, `copulas`, `ctgan`, `deepecho`, `sdmetrics`.
4. Adjust downloads for each dependency by subtracting the `sdv` download count.
5. Ensure no download count goes negative using `max(0, adjusted_count)` for each library.

This methodology prevents double-counting downloads while providing an accurate representation of SDV usage.

## Resources
For more information about the configuration, workflows, and metrics, see the resources below.
|               | Document                            | Description |
| ------------- | ----------------------------------- | ----------- |
| :pilot:       | [WORKFLOWS](docs/WORKFLOWS.md)           | How to collect data and add new libraries to the GitHub actions. |
| :gear:        | [SETUP](docs/SETUP.md)                   | How to generate credentials to access BigQuery and Google Drive and add them to GitHub Actions. |
| :keyboard:    | [DEVELOPMENT](docs/DEVELOPMENT.md)       | How to install and run the scripts locally. Overview of the project implementation. |
| :floppy_disk: | [COLLECTED DATA](docs/COLLECTED_DATA.md) | Explanation about the data that is being collected. |
