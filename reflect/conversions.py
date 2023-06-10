import pandas as pd
import json
import os
from datetime import datetime
from dateutil import tz
from typing import Dict, List, Optional, Tuple, Any

def parse_metrics(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Parse the metrics from a reflection instance into a dictionary.

    Args:
        metrics (list): A list of metrics in a reflection instance.

    Returns:
        dict: A dictionary with metric names as keys and metric values as values.
    """
    metric_dict = {}

    for metric in metrics:
        metric_kind = list(metric['kind'].keys())[0]
        # The "_0" string is an artifact of how Swift's JSONEncoder handles 
        # encoding of enum cases with associated values. See Apple 
        # documentation of JSONencoder in Swift:
        # https://developer.apple.com/documentation/foundation/jsonencoder
        metric_info = metric['kind'][metric_kind]['_0']

        if 'recorded' not in metric or metric['recorded']:
            try:
                    if metric_kind == 'string':
                        metric_dict[metric_info['name']] = metric_info['string']
                    elif metric_kind == 'choice':
                        metric_dict[metric_info['name']] = metric_info['choice']
                    elif metric_kind == 'bool':
                        metric_dict[metric_info['name']] = metric_info['bool']
                    elif metric_kind == 'unit':
                        metric_dict[metric_info['name']] = metric_info['value']
                    elif metric_kind == 'rating':
                        metric_dict[metric_info['name']] = metric_info['score']
            except KeyError:
                # print(f"KeyError encountered with the following metric: {json.dumps(metric, indent=2)}")
                metric_dict[metric_info['name']] = None

    return metric_dict

def parse_reflection(reflection: Dict) -> Tuple[str, pd.DataFrame]:
    """
    Parses an individual reflection instance into a DataFrame, which is 
    appended as a row to the output CSV file for the reflection type.

    Args:
        reflection (dict): A dictionary representing a reflection.

    Returns:
        str: The name of the reflection.
        pd.DataFrame: A DataFrame where each row corresponds to a reflection 
            instance and each column corresponds to a metric.
    """
    name = reflection['name']
    apple_timestamp = reflection['date']

    # Convert the Apple timestamp to a Python timestamp
    # 978307200 is the number of seconds between 1970-01-01T00:00:00Z and 
    # 2001-01-01T00:00:00Z
    timestamp = apple_timestamp + 978307200  

    # Convert the timestamp to datetime and adjust it to the local timezone
    local_tz = tz.tzlocal()
    date = datetime.fromtimestamp(timestamp).astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S")

    reflection_row = parse_metrics(reflection['metrics'])
    reflection_row['Timestamp'] = timestamp
    reflection_row['Date'] = date
    reflection_row['ID'] = reflection['id']
    reflection_row['Notes'] = reflection.get('notes')

    return name, pd.DataFrame([reflection_row])

def parse_json(json_string: str) -> Dict[str, pd.DataFrame]:
    """
    Parses a JSON string into a map from reflection names to DataFrames.

    Args:
        json_string (str): A JSON string.

    Returns:
        dict: A map where the keys are the reflection names and the values are 
            DataFrames with a row for each instance of the reflection in the
            history JSON.
    """
    data = json.loads(json_string)
    reflections_map = {}
    for reflection in data:
        name, df = parse_reflection(reflection)
        if name in reflections_map:
            reflections_map[name] = pd.concat([df, reflections_map[name]], ignore_index=True)
        else:
            reflections_map[name] = df
    return reflections_map


def save_dataframes_to_csv(reflections_map: Dict[str, pd.DataFrame], 
                           output_folder: str, 
                           filter_list: Optional[List[str]]=None) -> None:
    """
    Saves each DataFrame in the reflections_map to a CSV file.

    Args:
        reflections_map (dict): A map where the keys are the reflection names 
            and the values are DataFrames.
        output_folder (str): The path to the folder where the CSV files will be 
            saved.
        filter_list (list, optional): A list of reflection names. Only the 
            reflections with names in this list will be saved. Defaults to None.

    Returns:
        None
    """
    if filter_list is not None:
        reflections_map = {k: v for k, v in reflections_map.items() if k in filter_list}
    for name, df in reflections_map.items():
        df.to_csv(os.path.join(output_folder, f'{name}.csv'), index=False)
