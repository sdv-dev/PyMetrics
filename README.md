# Download Analytics

Scripts to extract metrics about OSS project downloads.

## Overview

The Download Analytics project is a collection of scripts and tools to extract information
about OSS project downloads from diffierent sources and to analyze them to produce user
engagement metrics.

### Data sources

Currently the data is being downloaded from the following sources:

* [PyPI](https://pypi.org/): Information about the project downloads from [PyPI](https://pypi.org/)
  obtained from the public Big Query dataset, equivalent to the information shown on
  [pepy.tech](https://pepy.tech).

In the future, these sources may also be added:

* [conda-forge](https://conda-forge.org/): Information about the project downloads from the
  `conda-forge` channel on `conda`.
* [github](https://github.com/): Information about the project downloads from github releases.

For more information about how to configure and use the software, or about the data that is being
collected check the resources below.

### Add new libraries
In order add new libraries, it is important to follow these steps to ensure that data is backfilled.
1. Update `config.yaml` with the new libraries (pypi project names only for now)
2. Run the [Manual collection workflow](https://github.com/datacebo/download-analytics/actions/workflows/manual.yaml) on your branch.
    - Use workflow from **your branch name**.
    - List the project names you added
    - Put '' for max_days to indicate you want all data
    - Pass any extra arguments (for example `--dry-run` to test your changes)
3. Let the workflow finish and check that pypi.csv contains the right data.
4. Get your pull request reviewed and merged into `main`. The daily collection workflow will fill the data for the last 30 days and future days.
    - Note: The collection script looks at timestamps and avoids adding overlapping data.

## Resources

|               | Document                            | Description |
| ------------- | ----------------------------------- | ----------- |
| :pilot:       | [WORKFLOWS](docs/WORKFLOWS.md)           | How to collect data and add new libraries to the Github actions. |
| :gear:        | [SETUP](docs/SETUP.md)                   | How to generate credentials to access BigQuery and Google Drive and add them to Github Actions. |
| :keyboard:    | [DEVELOPMENT](docs/DEVELOPMENT.md)       | How to install and run the scripts locally. Overview of the project implementation. |
| :floppy_disk: | [COLLECTED DATA](docs/COLLECTED_DATA.md) | Explanation about the data that is being collected. |
