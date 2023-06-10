import pandas as pd
import json
import os
from datetime import datetime
from dateutil import tz

def parse_metrics(metrics):
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

def parse_reflection(reflection):
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
    timestamp = reflection['date']

    # Convert the timestamp to datetime and adjust it to the local timezone
    local_tz = tz.tzlocal()
    date = datetime.fromtimestamp(timestamp).astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S")

    reflection_row = parse_metrics(reflection['metrics'])
    reflection_row['Timestamp'] = timestamp
    reflection_row['Date'] = date
    reflection_row['ID'] = reflection['id']
    reflection_row['Notes'] = reflection.get('notes')

    return name, pd.DataFrame([reflection_row])

def parse_json(json_string):
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
            reflections_map[name] = pd.concat([reflections_map[name], df])
        else:
            reflections_map[name] = df
    return reflections_map

def save_dataframes_to_csv(reflections_map, output_folder, filter_list=None):
    """
    Saves each DataFrame in the reflections_map to a CSV file.

    Args:
        reflections_map (dict): A map where the keys are the reflection names and the values are DataFrames.
        output_folder (str): The path to the folder where the CSV files will be saved.
        filter_list (list, optional): A list of reflection names. Only the reflections with names in this list will be saved. Defaults to None.

    Returns:
        None
    """
    if filter_list is not None:
        reflections_map = {k: v for k, v in reflections_map.items() if k in filter_list}
    for name, df in reflections_map.items():
        df.to_csv(os.path.join(output_folder, f'{name}.csv'), index=False)
