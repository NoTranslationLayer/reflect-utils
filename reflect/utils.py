import pandas as pd
import numpy as np
from typing import Optional


def dataframes_equal(df1: pd.DataFrame, df2: pd.DataFrame) -> bool:
    """
    Compare two pandas DataFrame for equality without considering column order.

    Args:
        df1: The first pandas DataFrame.
        df2: The second pandas DataFrame.

    Returns:
        True if the two DataFrame objects have the same shape and elements,
        False otherwise.
    """
    return df1.sort_index(axis=1).equals(df2.sort_index(axis=1))


def find_outliers(
    df: pd.DataFrame,
    time_window: str,
    z_threshold: float = 2.0,
    min_periods: Optional[int] = 1,
    center: bool = False,
) -> pd.DataFrame:
    """
    Identify outliers in a DataFrame based on the Z-Score method.

    Parameters
    ----------
    df : pd.DataFrame
        The input DataFrame. Must have 'Date' as the index.
    time_window : str
        Size of the moving window for the rolling mean and standard deviation
        calculations. This is the number of observations used for calculating
        the mean and standard deviation.
    z_threshold : float, optional
        The Z-Score threshold for identifying outliers. Default is 2.0.
    min_periods : int, optional
        Minimum number of observations in window required to have a value.
        Default is 1.
    center : bool, optional
        Whether to set the rolling window as centered. Default is False. When
        center=True, the window is centered on each data point, meaning the
        window includes approximately half the points before and half the
        points after each data point. When center=False, the window is
        positioned so that it includes the data point and the preceding points,
        but not any following points.

    Returns
    -------
    pd.DataFrame
        A copy of the input DataFrame, but with non-outlier numerical values
        replaced with NaN, and columns without outliers removed.
    """

    df_outliers = df.copy()
    numerical_cols = df_outliers.select_dtypes(
        include=np.number
    ).columns.tolist()
    cols_to_drop = []

    for col in numerical_cols:
        # Calculate rolling mean and std
        mean = (
            df_outliers[col]
            .rolling(
                window=time_window, center=center, min_periods=min_periods
            )
            .mean()
        )
        std = (
            df_outliers[col]
            .rolling(
                window=time_window, center=center, min_periods=min_periods
            )
            .std()
        )

        # Calculate Z-Scores
        zscore = (df_outliers[col] - mean) / std

        # Detect outliers using Z-Score
        df_outliers[col] = np.where(
            (np.abs(zscore) > z_threshold) & (std > 0),
            df_outliers[col],
            np.nan,
        )

        # Print Date, mean, and outlier value for detected outliers
        outliers = df_outliers.loc[df_outliers[col].notna(), [col]]
        if not outliers.empty:
            print(f"\nOutliers for column '{col}':\n")
            print(outliers)
        else:
            cols_to_drop.append(col)

    # Remove columns without outliers
    df_outliers.drop(cols_to_drop, axis=1, inplace=True)
    return df_outliers
