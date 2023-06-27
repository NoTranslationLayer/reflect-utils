import pandas as pd
import numpy as np
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
            "rating": 0,
            "scalar": 0,
        }
        self.pre_metric_defaults = {
            "string": None,
            "choice": None,
            "bool": None,
            "unit": np.nan,
            "rating": np.nan,
            "scalar": np.nan,
        }
        self.post_metric_defaults = {
            "string": None,
            "choice": None,
            "bool": None,
            "unit": np.nan,
            "rating": np.nan,
            "scalar": np.nan,
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
        try:
            return self.defaults[metric_kind]
        except KeyError:
            print(
                f"KeyError: {metric_kind} not found in defaults. "
                f"Supported keys are {list(self.defaults.keys())}"
            )
            raise

    def get_pre_metric_default(self, metric_kind: str):
        """
        Returns the default value for a given metric kind before its first
        occurrence.
        """
        try:
            return self.pre_metric_defaults[metric_kind]
        except KeyError:
            print(
                f"KeyError: {metric_kind} not found in pre_metric_defaults. "
                f"Supported keys are {list(self.pre_metric_defaults.keys())}"
            )
            raise

    def get_post_metric_default(self, metric_kind: str):
        """
        Returns the default value for a given metric kind after it has been
        removed from subsequent reflection instances.
        """
        try:
            return self.post_metric_defaults[metric_kind]
        except KeyError:
            print(
                f"KeyError: {metric_kind} not found in post_metric_defaults. "
                f"Supported keys are {list(self.post_metric_defaults.keys())}"
            )
            raise


def parse_metric_value(
    metric: Dict[str, Any]
) -> Optional[Tuple[str, str, Any]]:
    """
    This function parses the value of a given metric based on its kind.

    Args:
        metric (Dict[str, Any]): A dictionary that contains information about
        a metric, including its kind and value.

    Returns:
        Optional[Tuple[str, str, Any]]: A tuple with the name, kind, and the parsed
        value of the metric, if it exists and is recorded. Otherwise, returns
        None.

    Raises:
        KeyError: If "kind" key does not exist in the metric.
        ValueError: If "kind" key exists but its value is empty.
    """
    if "kind" not in metric or not metric["kind"]:
        raise KeyError(f'"kind" not found in metric: {metric}')

    metric_kind = list(metric["kind"].keys())[0]

    # The "_0" string is an artifact of how Swift's JSONEncoder handles
    # encoding of enum cases with associated values. See Apple
    # documentation of JSONencoder in Swift:
    # https://developer.apple.com/documentation/foundation/jsonencoder
    metric_content = metric["kind"][metric_kind].get("_0")

    if metric_content is None:
        raise ValueError(f"unexpected metric contents in JSON: {metric}")

    metric_name = metric_content.get("name")
    if metric_name is not None:
        try:
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
            value = None
            print(
                f"failed to retrieve value from metric: {metric} of kind "
                f"{metric_kind}"
            )
        if "recorded" in metric and not metric["recorded"]:
            value = None
        return metric_name, metric_kind, value

    return None


def parse_metrics(
    metrics: List[Dict[str, Any]],
    parsing_options: ParsingOptions,
    existing_columns: List[str],
    metric_type_map: Dict[str, str],
) -> Dict[str, Any]:
    """
    Parse the metrics from a reflection instance into a dictionary.

    Args:
        metrics (list): A list of metrics in a reflection instance.
        parsing_options (ParsingOptions): The default value options.
        existing_columns (List[str]): List of existing columns in the DataFrame
            for the reflection.
        metric_type_map (Dict[str, str]): Dictionary to keep track of metric
            type changes.

    Returns:
        dict: A dictionary with metric names as keys and metric values as values.
    """
    metric_dict = {}

    for metric in metrics:
        result = parse_metric_value(metric)

        if result is not None:
            metric_name, metric_kind, metric_val = result
            if (
                metric_name in metric_type_map
                and metric_type_map[metric_name] != metric_kind
            ):
                print(
                    f"Warning: Metric type for {metric_name} changed from "
                    f"{metric_type_map[metric_name]} to {metric_kind}"
                )

            metric_type_map[metric_name] = metric_kind

            if metric_val is not None:
                metric_dict[metric_name] = metric_val
            else:
                metric_dict[metric_name] = parsing_options.get_default_value(
                    metric_kind
                )

    # Check if a metric was removed from the template. If the metric is present
    # in the reflection at the time it was recorded, we have an implicit
    # representation of the template at that point in time, so any metric name
    # that was present in the previous instances but is not present in this
    # reflection means that the metric was removed at some point in time.
    for column in existing_columns:
        if column not in metric_dict and column not in [
            "Timestamp",
            "ID",
            "Notes",
            "Date",
        ]:
            metric_dict[column] = parsing_options.get_post_metric_default(
                metric_type_map[column]
            )

    return metric_dict


def parse_reflection(
    reflection: Dict,
    parsing_options: ParsingOptions,
    existing_df: pd.DataFrame = None,
    metric_type_map: Dict[str, str] = None,
) -> Tuple[str, pd.DataFrame]:
    """
    Parses an individual reflection instance into a DataFrame, which is
    appended as a row to the output CSV file for the reflection type.

    Args:
        reflection (dict): A dictionary representing a reflection.
        parsing_options (ParsingOptions): The default value options.
        existing_df (DataFrame, optional): The existing DataFrame for the
            reflection. Defaults to None.
        metric_type_map (Dict[str, str]): Dictionary to keep track of metric
            type changes.

    Returns:
        Tuple[str, pd.DataFrame, Dict[str, str]]: The name of the reflection,
        a DataFrame where each row corresponds to a reflection instance and
        each column corresponds to a metric, and the updated metric type map.
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
        reflection["metrics"],
        parsing_options,
        existing_columns,
        metric_type_map,
    )
    reflection_row["Timestamp"] = timestamp
    reflection_row["Date"] = date
    reflection_row["ID"] = reflection["id"]
    reflection_row["Notes"] = reflection.get("notes")

    return name, pd.DataFrame([reflection_row]), metric_type_map


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

    # Sort the list of dictionaries by "date" in ascending order
    data = sorted(data, key=lambda x: x["date"], reverse=True)

    reflections_map = {}
    metric_type_map = {}  # track metric types

    for reflection in data:
        existing_df = reflections_map.get(reflection["name"])
        name, df, metric_type_map = parse_reflection(
            reflection, parsing_options, existing_df, metric_type_map
        )
        if name in reflections_map:
            new_columns = set(df.columns) - set(reflections_map[name].columns)
            for column in new_columns:
                if column in metric_type_map:
                    # Fill the existing dataframe with pre_metric_default
                    # values for new columns
                    reflections_map[name][
                        column
                    ] = parsing_options.get_pre_metric_default(
                        metric_type_map[column]
                    )
            reflections_map[name] = pd.concat(
                [reflections_map[name], df], ignore_index=True
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
