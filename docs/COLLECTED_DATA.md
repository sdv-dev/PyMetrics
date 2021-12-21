# Data collected by Download Analytics

The Download Analytics project collects data about downloads from multiple sources.

This guide explains the exact data that is being collected from each source, as well as
the aggregations metrics that are computed on them.

## PyPI Downloads

Download Analytics collects information about the downloads from PyPI by making queries to the
[public PyPI download statistics dataset on Big Query](https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=pypi&page=dataset)
by running the following query:

```
SELECT
    timestamp,
    country_code,
    file.project                    as project,
    file.version                    as version,
    file.type                       as type,
    details.installer.name          as installer_name,
    details.implementation.name     as implementation_name,
    details.implementation.version  as implementation_version,
    details.distro.name             as distro_name,
    details.distro.version          as distro_version,
    details.system.name             as system_name,
    details.system.release          as system_release,
    details.cpu                     as cpu,
FROM `bigquery-public-data.pypi.file_downloads`
WHERE file.project in {projects}
    AND timestamp >= '{start_date}'
    AND timestamp < '{end_date}'
```

which outputs a table with one row for each individual download of the indicated projects within
the given time period, with the following columns:

* `timestamp`: The timestamp at which the download happened.
* `country_code`: The 2-letters country code.
* `project`: The name of the PyPI project (library) that is being downloaded.
* `version`: The downloaded version.
* `type`: The type of file that was downloaded, source or wheel.
* `installer_name`: The installer used for the download, like `pip` or `bandersnatch`.
* `implementation_name`: The name of the Python implementation, such as `cpython`.
* `implementation_version`: The Python version.
* `distro_name`: Name of the Linux or Mac distribution. Empty if Windows.
* `distro_version`: Distribution version. Empty for Windows.
* `system_name`: Type of OS, like Linux, Darwin (for Mac) or Windows.
* `system_release`: OS Version in case of Windows, Kernel version in case of Unix.
* `cpu`: CPU Architecture used.

## Aggregation Metrics

If the `--add-metrics` option is passed to `download-analytics`, a spreadsheet with aggregation
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
* **By Month and Version:** Absolute number of downloads per month and version.
* **By Month and Python Version:** Absolute number of downloads per month and Python version.
* **By Month and Country Code:** Absolute number of downloads per month and country.
* **By Month and Installer Name:** Absolute number of downloads per month and Installer.
