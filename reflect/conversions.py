import pandas as pd
import json
import os
import yaml
from datetime import datetime
from dateutil import tz
from typing import Dict, List, Optional, Tuple, Any


class ParsingOptions:
    """
    This class holds the default values for different metric kinds. It supports
    three types of default values:
    1. The value to use before the first occurrence of a metric.
    2. The value to use if a metric is not recorded.
    3. The value to use if a metric has been removed from subsequent reflection
       instances.
    These defaults can be updated using a YAML file.
    """

    def __init__(self):
        """
        Initializes the default, pre_metric, and post_metric values for
        different metric kinds.
        """
        self.defaults = {
            "string": "",
            "choice": None,
            "bool": False,
            "unit": 0,
            "rating": None,
            "scalar": None,
        }
        self.pre_metric_defaults = {
            "string": "",
            "choice": None,
            "bool": False,
            "unit": 0,
            "rating": None,
            "scalar": None,
        }
        self.post_metric_defaults = {
            "string": "",
            "choice": None,
            "bool": False,
            "unit": 0,
            "rating": None,
            "scalar": None,
        }

    def load_from_yaml(self, yaml_file: str):
        """
        Load the default values from a YAML file. The file should contain
        dictionaries for 'defaults', 'pre_metric_defaults', and
        'post_metric_defaults' where the keys are metric kinds and the values
        are the default values.
        """
        with open(yaml_file, "r") as file:
            new_defaults = yaml.safe_load(file)

        self.defaults.update(new_defaults.get("defaults", {}))
        self.pre_metric_defaults.update(
            new_defaults.get("pre_metric_defaults", {})
        )
        self.post_metric_defaults.update(
            new_defaults.get("post_metric_defaults", {})
        )

    def get_default_value(self, metric_kind: str):
        """Returns the default value for a given metric kind."""
        return self.defaults.get(metric_kind)

    def get_pre_metric_default(self, metric_kind: str):
        """
        Returns the default value for a given metric kind before its first
        occurrence.
        """
        return self.pre_metric_defaults.get(metric_kind)

    def get_post_metric_default(self, metric_kind: str):
        """
        Returns the default value for a given metric kind after it has been
        removed from subsequent reflection instances.
        """
        return self.post_metric_defaults.get(metric_kind)


def parse_metric_value(metric: Dict[str, Any]) -> Optional[Any]:
    """
    This function parses the value of a given metric based on its kind.

    Args:
        metric (Dict[str, Any]): A dictionary that contains information about
        a metric, including its kind and value.

    Returns:
        (str, str, Any): A tuple with the name, kind, and the parsed value of
        the metric, if it exists and is recorded. Otherwise, returns None.

    Raises:
        KeyError: If "kind" key does not exist in the metric or its value is
        empty.
    """
    if "kind" not in metric or not metric["kind"]:
        raise KeyError(f'"kind" not found in metric: {metric}')
    metric_kind = list(metric["kind"].keys())[0]
    metric_content = metric["kind"][metric_kind].get("_0")

    if metric_content is not None:
        try:
            metric_name = metric_content["name"]
            if metric_kind == "string":
                value = metric_content["string"]
            elif metric_kind == "choice":
                value = metric_content["choice"]
            elif metric_kind == "bool":
                value = metric_content["bool"]
            elif metric_kind == "unit":
                value = metric_content["value"]
            elif metric_kind == "rating":
                value = metric_content["score"]
            elif metric_kind == "scalar":
                value = metric_content["scalar"]
        except KeyError:
            return None
    if "recorded" in metric and not metric["recorded"]:
        return None
    return metric_name, metric_kind, value


def parse_metrics(
    metrics: List[Dict[str, Any]],
    parsing_options: ParsingOptions,
    existing_columns: List[str],
) -> Dict[str, Any]:
    """
    Parse the metrics from a reflection instance into a dictionary.

    Args:
        metrics (list): A list of metrics in a reflection instance.
        parsing_options (ParsingOptions): The default value options.
        existing_columns (List[str]): List of existing columns in the DataFrame
            for the reflection.

    Returns:
        dict: A dictionary with metric names as keys and metric values as values.
    """
    metric_dict = {}

    for metric in metrics:
        result = parse_metric_value(metric)

        if result is not None:
            metric_name, metric_kind, metric_val = result
            metric_dict[metric_name] = metric_val
        elif metric_name in existing_columns:
            metric_dict[metric_name] = parsing_options.get_post_metric_default(
                metric_kind
            )
        else:
            metric_dict[metric_name] = parsing_options.get_default_value(
                metric_kind
            )

    for column in existing_columns:
        if column not in metric_dict:
            metric_dict[column] = parsing_options.get_pre_metric_default(
                metric_kind
            )

    return metric_dict


def parse_reflection(
    reflection: Dict,
    parsing_options: ParsingOptions,
    existing_df: pd.DataFrame = None,
) -> Tuple[str, pd.DataFrame]:
    """
    Parses an individual reflection instance into a DataFrame, which is
    appended as a row to the output CSV file for the reflection type.

    Args:
        reflection (dict): A dictionary representing a reflection.
        parsing_options (ParsingOptions): The default value options.
        existing_df (DataFrame, optional): The existing DataFrame for the
            reflection. Defaults to None.

    Returns:
        str: The name of the reflection.
        pd.DataFrame: A DataFrame where each row corresponds to a reflection
            instance and each column corresponds to a metric.
    """
    name = reflection["name"]
    apple_timestamp = reflection["date"]

    # Convert the Apple timestamp to a Python timestamp
    # 978307200 is the number of seconds between 1970-01-01T00:00:00Z and
    # 2001-01-01T00:00:00Z
    timestamp = apple_timestamp + 978307200

    # Convert the timestamp to datetime and adjust it to the local timezone
    local_tz = tz.tzlocal()
    date = (
        datetime.fromtimestamp(timestamp)
        .astimezone(local_tz)
        .strftime("%Y-%m-%d %H:%M:%S")
    )

    existing_columns = (
        existing_df.columns.tolist() if existing_df is not None else []
    )
    reflection_row = parse_metrics(
        reflection["metrics"], parsing_options, existing_columns
    )
    reflection_row["Timestamp"] = timestamp
    reflection_row["Date"] = date
    reflection_row["ID"] = reflection["id"]
    reflection_row["Notes"] = reflection.get("notes")

    # Use post_metric_default for any columns in existing_df not present in this reflection instance
    if existing_df is not None:
        for column in existing_df.columns:
            if column not in reflection_row:
                reflection_row[
                    column
                ] = parsing_options.get_post_metric_default(column)

    return name, pd.DataFrame([reflection_row])


def parse_json(
    json_string: str, parsing_options: ParsingOptions
) -> Dict[str, pd.DataFrame]:
    """
    Parses a JSON string into a map from reflection names to DataFrames.

    Args:
        json_string (str): A JSON string.
        parsing_options (ParsingOptions): The default value options.

    Returns:
        dict: A map where the keys are the reflection names and the values are
            DataFrames with a row for each instance of the reflection in the
            history JSON.
    """
    data = json.loads(json_string)
    reflections_map = {}
    for reflection in data:
        existing_df = reflections_map.get(reflection["name"])
        name, df = parse_reflection(reflection, parsing_options, existing_df)
        if name in reflections_map:
            reflections_map[name] = pd.concat(
                [df, reflections_map[name]], ignore_index=True
            )
        else:
            reflections_map[name] = df
    return reflections_map


def save_dataframes_to_csv(
    reflections_map: Dict[str, pd.DataFrame],
    output_folder: str,
    filter_list: Optional[List[str]] = None,
) -> None:
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
        reflections_map = {
            k: v for k, v in reflections_map.items() if k in filter_list
        }
    for name, df in reflections_map.items():
        df.to_csv(os.path.join(output_folder, f"{name}.csv"), index=False)
