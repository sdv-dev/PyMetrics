# Download Analytics

The Download Analytics project allows you to extract download metrics from a Python library published on [PyPI](https://pypi.org/). 
The DataCebo team uses these scripts to report growth for the libraries in the [SDV ecosystem](https://sdv.dev/) but you may 
use it for any Python software.

This software is available in open source under the MIT License. **We are not actively maintaining this repository.**

### Data sources

Currently the download data is coming from the following distributions:

* [PyPI](https://pypi.org/): Information about the project downloads from [PyPI](https://pypi.org/)
  obtained from the public Big Query dataset, equivalent to the information shown on
  [pepy.tech](https://pepy.tech).

In the future, we may also expand the source distributions to include:

* [conda-forge](https://conda-forge.org/): Information about the project downloads from the
  `conda-forge` channel on `conda`.
* [github](https://github.com/): Information about the project downloads from github releases.

### Metrics
This library collects the number of downloads for your chosen software. You can break these up along several dimensions:

- **By Month**: The number of downloads per month
- **By Version**: The number of downloads per version of the software, as determine by the software maintainers
- **By Python Version**: The number of downloads per minor Python version (eg. 3.8)
- **And more!** See the resources below for more information.

## Resources
For more information about the configuration, workflows and metrics, see the resources below.

|               | Document                            | Description |
| ------------- | ----------------------------------- | ----------- |
| :pilot:       | [WORKFLOWS](docs/WORKFLOWS.md)           | How to collect data and add new libraries to the Github actions. |
| :gear:        | [SETUP](docs/SETUP.md)                   | How to generate credentials to access BigQuery and Google Drive and add them to Github Actions. |
| :keyboard:    | [DEVELOPMENT](docs/DEVELOPMENT.md)       | How to install and run the scripts locally. Overview of the project implementation. |
| :floppy_disk: | [COLLECTED DATA](docs/COLLECTED_DATA.md) | Explanation about the data that is being collected. |
