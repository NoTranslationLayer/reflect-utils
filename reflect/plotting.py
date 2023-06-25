import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import seaborn as sns
from typing import Optional

def plot(
    df: pd.DataFrame,
    title: str = "",
    frequency: Optional[str] = None,
    sampling_method: str = 'mean',
    max_metrics_per_subplot: Optional[int] = None
) -> None:
    """
    Plot the DataFrame data with optional resampling and subplotting.

    Args:
        df: Input DataFrame.
        title: Optional title for the plot (default: "")
        frequency: Frequency string for resampling (e.g., 'hourly', 'daily', 
            'weekly', 'biweekly'). Also supports custom pandas offset aliases 
            of the format 3D for 3 days, 2M for 2 months. See documentation 
            here: https://pandas.pydata.org/pandas-docs/version/0.22/timeseries.html#offset-aliases 
            Defaults to None.
        sampling_method: Resampling method ('mean', 'min', 'max'). Defaults to 
            'mean'.
        max_metrics_per_subplot: Maximum number of metrics per subplot. 
            Defaults to None.

    Returns:
        None
    """
    # Create a dictionary to map frequency strings to pandas offset aliases
    freq_dict = {
        'hourly': 'H',
        'daily': 'D',
        'weekly': 'W',
        'biweekly': '2W',
        'monthly': 'M',
        'yearly': 'Y'
    }
    
    # Resample the data if frequency is not None
    if frequency is not None:
        # Convert frequency string to pandas offset alias.
        # Use the original string if it's not found in freq_dict
        # which allows custom frequencies, e.g. 3D for 3 days, 3W for 3 weeks, 
        # etc.
        resample_frequency = freq_dict.get(frequency, frequency)
        
        # Resample the data
        if sampling_method == 'mean':
            df = df.resample(resample_frequency).mean()
        elif sampling_method == 'min':
            df = df.resample(resample_frequency).min()
        elif sampling_method == 'max':
            df = df.resample(resample_frequency).max()
        else:
            raise ValueError("Invalid method. Choose from 'mean', 'min', 'max'.")
    
    # Plot all metrics on the same plot if max_metrics_per_subplot is None
    if max_metrics_per_subplot is None:
        ax = df.plot(style='x-', grid=True, markersize=10, figsize=(15, 5))
        ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
#         ax.minorticks_on()
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black')
        plt.tight_layout()
        plt.show()
        return

    # Otherwise, create subplots
    num_metrics = len(df.columns)
    num_subplots = math.ceil(num_metrics / max_metrics_per_subplot)
    
    fig, axs = plt.subplots(num_subplots, 1, figsize=(15, 5 * num_subplots), sharex=True)
    if num_subplots == 1:
        axs = [axs]

    for i, ax in enumerate(axs):
        start = i * max_metrics_per_subplot
        end = min((i + 1) * max_metrics_per_subplot, num_metrics)
        df.iloc[:, start:end].plot(ax=ax, style='x-', grid=True, markersize=10)
        ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black')
    
    # Set the title if provided
    if title:
        plt.suptitle(title)

    plt.tight_layout()
    plt.show()



def filtered_correlation_plot(df: pd.DataFrame, title: str = "") -> pd.DataFrame:
    """
    This function plots the filtered correlation matrix of a dataframe.

    Args:
        df: A pandas DataFrame object
        title: Optional title for the plot (default: "")

    The function computes the correlation matrix of the input DataFrame,
    sets diagonal values to NaN (correlations of variables with themselves),
    and then filters the correlations based on their strength.

    Two heatmaps are plotted - one with the original correlations and one with 
    the filtered correlations.

    The filtering process is as follows:
    - Correlations with absolute values less than 0.1 are set to 0
    - Correlations with absolute values less than 0.3 are set to 0.2 
      (keeping the original sign)
    - Correlations with absolute values less than 0.5 are set to 0.4 
      (keeping the original sign)
    - All other correlations are set to 0.8 (keeping the original sign)
    """
    
    # Compute the correlation matrix
    corr = df.corr()
    
    # Set diagonal values to NaN
    np.fill_diagonal(corr.values, np.nan)

    # Create the first subplot
    plt.figure(figsize=(10, 4.5))
    plt.subplot(1, 2, 1)
    sns.heatmap(corr, vmin=-1, vmax=1, center=0, cmap='coolwarm', annot=True)
    plt.title('Original Correlations')
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)

    # Filter the correlation values
    corr_filtered = corr.copy()
    for i in range(corr_filtered.shape[0]):
        for j in range(corr_filtered.shape[1]):
            value = corr_filtered.iloc[i, j]
            sign = np.sign(value)
            if abs(value) < 0.1:
                corr_filtered.iloc[i, j] = 0
            elif abs(value) < 0.3:
                corr_filtered.iloc[i, j] = sign * 0.2
            elif abs(value) < 0.5:
                corr_filtered.iloc[i, j] = sign * 0.4
            else:
                corr_filtered.iloc[i, j] = sign * 0.8

    # Create the second subplot
    plt.subplot(1, 2, 2)
    sns.heatmap(corr_filtered, vmin=-1, vmax=1, center=0, cmap='coolwarm', annot=True)
    plt.title('Filtered Correlations')
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)

    # Set the title if provided
    if title:
        plt.suptitle(title)

    plt.tight_layout()
    plt.show()
