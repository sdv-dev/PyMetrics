#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as readme_file:
    readme = readme_file.read()

install_requires = [
    'pandas==1.4.2',
    'google-cloud-bigquery==3.0.1',
    'db-dtypes==1.0.0',
    'openpyxl==3.0.9',
    'xlsxwriter==3.0.3',
    'PyYAML==6.0',
    'PyDrive==1.3.1',
    'httplib2==0.15.0',  # noqa: https://stackoverflow.com/questions/59815620/gcloud-upload-httplib2-redirectmissinglocation-redirected-but-the-response-is-m
]


setup(
    author='DataCebo',
    author_email='info@datacebo.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description='Scripts to extract metrics about OSS project downloads.',
    entry_points={
        'console_scripts': [
            'download-analytics=download_analytics.__main__:main'
        ]
    },
    include_package_data=True,
    install_requires=install_requires,
    keywords='download-analytics',
    long_description=readme,
    long_description_content_type='text/markdown',
    name='download-analytics',
    packages=find_packages(include=['download_analytics', 'download_analytics.*']),
    python_requires='>=3.7,<3.10',
    version='0.0.1.dev0',
    zip_safe=False,
)
