"""
Module for detecting various quality control aspects from source data.
"""

import operator
import pathlib
from functools import reduce
from typing import Dict, List, Optional, Union

import pandas as pd
import yaml
from scipy.stats import zscore as scipy_zscore

DEFAULT_QC_THRESHOLD_FILE = (
    f"{pathlib.Path(__file__).parent!s}/data/qc_thresholds_default.yml"
)


def find_outliers(
    df: pd.DataFrame,
    metadata_columns: List[str],
    feature_thresholds: Union[Dict[str, float], str],
    feature_thresholds_file: Optional[str] = DEFAULT_QC_THRESHOLD_FILE,
) -> pd.DataFrame:
    """
    This function uses z-scoring to format the data for detecting outlier
    nuclei or cells using specific CellProfiler features. Thresholds are
    the number of standard deviations away from the mean, either above
    (positive) or below (negative). We recommend making sure to not use a
    threshold of 0 as that would represent the whole dataset.

    Args:
        df: pd.DataFrame
            Data frame with converted output from CytoTable.
        metadata_columns: List[str]
            List of metadata columns that should be outputted with the outlier data.
        feature_thresholds: Dict[str, float]
            One of two options:
            A dictionary with the feature name(s) as the key(s) and their assigned
            threshold for identifying outliers. Positive int for the threshold
            will detect outliers "above" than the mean, negative int will detect
            outliers "below" the mean.
            Or a string which is a named key reference found within
            the feature_thresholds_file yaml file.
        feature_thresholds_file: Optional[str] = DEFAULT_QC_THRESHOLD_FILE,
            An optional feature thresholds file where thresholds may be
            defined within a file.

    Returns:
        pd.DataFrame:
            Outlier data frame for the given conditions.
    """

    if isinstance(feature_thresholds, str):
        feature_thresholds = read_thresholds_set_from_file(
            feature_thresholds=feature_thresholds,
            feature_thresholds_file=feature_thresholds_file,
        )

    # Create z-score columns for each feature to reference during outlier detection
    zscore_columns = {}
    for feature in feature_thresholds:
        if feature not in df.columns:
            raise ValueError(f"Feature '{feature}' does not exist in the DataFrame.")
        df[f"Z_Score_{feature}"] = scipy_zscore(df[feature])
        zscore_columns[feature] = f"Z_Score_{feature}"

    # Create outlier detection conditions for each feature
    conditions = []
    for feature, threshold in feature_thresholds.items():
        # For positive thresholds, look for outliers that are
        # that number of std "above" the mean
        if threshold > 0:
            condition = df[zscore_columns[feature]] > threshold
        # For negative thresholds, look for outliers that are
        # that number of std "below" the mean
        else:
            condition = df[zscore_columns[feature]] < threshold
        conditions.append(condition)

    # Filter DataFrame for outliers using all conditions
    outliers_df = df[reduce(operator.and_, conditions)]

    # Print outliers count and range for each feature
    print("Number of outliers:", outliers_df.shape[0])
    print("Outliers Range:")
    for feature in feature_thresholds:
        print(f"{feature} Min:", outliers_df[feature].min())
        print(f"{feature} Max:", outliers_df[feature].max())

    # Include metadata columns in the output DataFrame
    columns_to_include = list(feature_thresholds.keys()) + metadata_columns

    # Return outliers DataFrame with specified columns
    return outliers_df[columns_to_include]


def read_thresholds_set_from_file(
    feature_thresholds: str, feature_thresholds_file: str
):
    """
    Reads a set of feature thresholds from a specified file.

    This function takes the path to a feature thresholds file and a
    specific feature threshold string, reads the file, and returns
    the thresholds set from the file.

    Args:
        feature_thresholds (str):
            A string specifying the feature thresholds.
        feature_thresholds_file (str):
            The path to the file containing feature thresholds.

    Returns:
        dict: A dictionary containing the processed feature thresholds.

    Raises:
        LookupError: If the file does not contain the specified feature_thresholds key.
    """

    with open(feature_thresholds_file, "r") as file:
        thresholds = yaml.safe_load(file)

    if feature_thresholds not in thresholds["thresholds"]:
        raise LookupError(
            (
                f"Unable to find threshold set by name {feature_thresholds}"
                f" within {feature_thresholds_file}"
            )
        )

    return thresholds["thresholds"][feature_thresholds]