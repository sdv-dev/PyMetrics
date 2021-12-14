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

## Resources

|               | Document                            | Description |
| ------------- | ----------------------------------- | ----------- |
| :pilot:       | [WORKFLOWS](docs/WORKFLOWS.md)           | How to collect data and add new libraries to the Github actions. |
| :gear:        | [SETUP](docs/SETUP.md)                   | How to generate credentials to access BigQuery and Google Drive and add them to Github Actions. |
| :keyboard:    | [DEVELOPMENT](docs/DEVELOPMENT.md)       | How to install and run the scripts locally. Overview of the project implementation. |
| :floppy_disk: | [COLLECTED DATA](docs/COLLECTED_DATA.md) | Explanation about the data that is being collected. |
