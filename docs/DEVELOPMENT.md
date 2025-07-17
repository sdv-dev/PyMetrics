# PyMetrics Development Guide

This guide covers how to download and install **PyMetrics** to run it locally and
modify its code.

## Install

**PyMetrics** is not released to any public Python package repository, so the only
way to run it is to download the code from Github and install from source.

1. Clone the [github repository](https://github.com/datacebo/pymetrics)

```bash
git clone git@github.com:datacebo/pymetrics
```

2. Create a `virtualenv` (or `conda` env) to host the project and its dependencies. The example
   below covers the creation of a `virtualenv` using `virtualenvwrapper` with Python 3.8.

```bash
mkvirtualenv pymetrics -p $(which python3.8)
```

3. Enter the project folder and install the project:

```bash
cd pymetrics
make install
```

For development, run `make install-develop` instead.

## Command Line Interface

After the installation, a new `pymetrics` command will have been registered inside your
`virtualenv`. This command can be used in conjunction with the `collect-pypi` action to collect
downloads data from BigQuery and store the output locally or in Google Drive.

Here is the entire list of arguments that the command line has:

```bash
$ pymetrics collect-pypi --help
usage: pymetrics collect-pypi [-h] [-v] [-l LOGFILE] [-o OUTPUT_FOLDER] [-a AUTHENTICATION_CREDENTIALS]
                                  [-c CONFIG_FILE] [-p [PROJECTS [PROJECTS ...]]] [-s START_DATE]
                                  [-m MAX_DAYS] [-d] [-f] [-M]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Be verbose. Use `-vv` for increased verbosity.
  -l LOGFILE, --logfile LOGFILE
                        If given, file where the logs will be written.
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Path to the folder where data will be stored. It can be a local path or a Google
                        Drive folder path in the format gdrive://<folder-id>
  -a AUTHENTICATION_CREDENTIALS, --authentication-credentials AUTHENTICATION_CREDENTIALS
                        Path to the GCP (BigQuery) credentials file to use.
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        Path to the configuration file.
  -p [PROJECTS [PROJECTS ...]], --projects [PROJECTS [PROJECTS ...]]
                        List of projects to collect. If not given use the configured ones.
  -s START_DATE, --start-date START_DATE
                        Date from which to start pulling data.
  -m MAX_DAYS, --max-days MAX_DAYS
                        Max days of data to pull if start-date is not given.
  -d, --dry-run         Do not run the actual query, only simulate it.
  -f, --force           Force the download even if the data already exists or there is a gap
  -M, --add-metrics     Compute the aggregation metrics and create the corresponding spreadsheets.
```


For example, a command to collect data for the projects `sdv` and `ctgan` from `2021-01-01` onwards
and store the downloads data into a Google Drive folder alongside the corresponding aggregation
metric spreadsheets would look like this:

```bash
$ pymetrics collect-pypi --verbose --projects sdv ctgan --start-date 2021-01-01 \
        --add-metrics --output-folder gdrive://10QHbqyvptmZX4yhu2Y38YJbVHqINRr0n
```

For more details about the data that this would collect and which files would be generated
have a look at the [COLLECTED_DATA.md](COLLECTED_DATA.md) document.

## Python Interface

The Python entry point that is equivalent to the CLI explained above is the function
`download_analytics.main.collect_downloads`.

This function has the following interface:

```
collect_downloads(projects, output_folder, start_date=None, max_days=1, credentials_file=None,
                  dry_run=False, force=False, add_metrics=True)
    Pull data about the downloads of a list of projects.

    Args:
        projects (list[str]):
            List of projects to analyze.
        output_folder (str):
            Folder in which project downloads will be stored.
            It can be passed as a local folder or as a Google Drive path in the format
            `gdrive://{folder_id}`.
        start_date (datetime or None):
            Date from which to start collecting data. If `None`,
            start_date will be current date - `max_days`.
        max_days (int):
            Maximum amount of days to include in the query from current date back, in case
            `start_date` has not been provided. Defaults to 1.
        credentials_file (str):
            Path to the GCP Credentials file for BigQuery.
        dry_run (bool):
            If `True`, do not run the actual query. Defaults to `False`.
        force (bool):
            Whether to force the query even if data already exists or the dates
            combination creates a gap. Defaults to False.
        add_metrics (bool):
            Whether to compute and create the aggregation metrics spreadsheets.
```

## Project Structure

The project is made, among other things, of the following parts:

* `.github`: The folder where the Github Action Workflows used for scheduled and manual download
  within the Github UI are defined.
* `config.yaml`: The file where the default output-folder, max-days and projects that are collected
  by the Github Actions Workflows are stored.
* `dev-requirements.txt`: The file where the development dependencies (mostly style-check tools)
  are listed.
* `docs`: Folder where this and the other documentation files are stored.
* `download_anlytics`: Folder in which the Python code of the project resides.
* `setup.py`: The file where the details of the project, as well as its dependencies, are listed.
* `tests`: The folder where unit tests are implemented.


The project, code, which can be found inside the `download_anlytics` folder, is divided in the
following modules:

* `bq.py`: Implements the code to run queries on Big Query.
* `drive.py`: Implements the functions to upload files to and download files from Google Drive.
* `__main__.py`: Implements the Command Line Interface of the project.
* `main.py`: Implements the `collect_downloads` function.
* `metrics.py`: Implements the functions to compute the aggregation metrics and trigger the
  creation of the corresponding spreadsheets.
* `output.py`: Implements the functions to read and write CSV files and spreadsheets, both
  locally or on Google Drive (using the `drive.py` module listed above).
* `pypi.py`: Implements the `get_pypi_downloads` function, which crafts and executes the
  Big Query query using the `bq` model.
