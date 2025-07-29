import numpy as np
import pandas as pd

from pymetrics.metrics import _sort_by_version


def test__sort_by_version():
    # Setup
    data = pd.DataFrame({
        'version': pd.Series(
            ['1.9.0', '1.9.0.dev0', '1.24.1', '0.9.1', '0.16.0', '0.0.0'], dtype='object'
        ),
        'name': ['v5', 'v4', 'v6', 'v2', 'v3', 'v1'],
    })

    # Run
    sorted_df = _sort_by_version(data, 'version', ascending=False)

    # Assert
    expected_versions = ['1.24.1', '1.9.0', '1.9.0.dev0', '0.16.0', '0.9.1', '0.0.0']
    assert sorted_df['version'].map(str).tolist() == expected_versions
    assert sorted_df['name'].tolist() == ['v6', 'v5', 'v4', 'v3', 'v2', 'v1']


def test__sort_by_version_with_invalid_versions():
    # Setup
    data = pd.DataFrame({
        'version': pd.Series(['2.0.0', 'invalid', '3.0', np.nan], dtype='object'),
        'name': ['v3', 'v2', 'v4', 'v1'],
    })

    # Run
    sorted_df = _sort_by_version(data, 'version')

    # Assert
    expected_versions = ['3.0', '2.0.0', 'invalid', np.nan]
    assert sorted_df['version'].tolist() == expected_versions
    assert sorted_df['name'].tolist() == ['v4', 'v3', 'v2', 'v1']


def test__sort_by_version_with_mixed_version_formats():
    # Setup
    data = pd.DataFrame({
        'version': ['1.0a1', '1.0b2', '1.0rc3', '1.0', '1.0.post0'],
        'name': ['alpha', 'beta', 'rc', 'stable', 'post'],
    })

    # Run
    sorted_df = _sort_by_version(data, 'version', ascending=False)

    # Assert
    expected_versions = ['1.0.post0', '1.0', '1.0rc3', '1.0b2', '1.0a1']
    assert sorted_df['version'].tolist() == expected_versions
    assert sorted_df['name'].tolist() == ['post', 'stable', 'rc', 'beta', 'alpha']
