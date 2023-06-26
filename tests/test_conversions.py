import unittest
import os
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil import tz
from pandas.testing import assert_frame_equal

from reflect import conversions as conv


class TestParsingMetricValue(unittest.TestCase):
    """
    Tests the `parse_metric_value` function's ability to correctly extract the
    metric name, kind, and value from the provided metric dictionary. It also
    tests the function's behavior when the metric "kind" is missing or when the
    metric is present but is not recorded.
    """

    def setUp(self):
        self.metric_data = {
            "kind": {"bool": {"_0": {"name": "No Gi", "bool": False}}},
            "id": "994FAC7F-FA9D-4B5E-9896-F72165F72A6C",
            "group": "Info",
        }
        self.metric_no_kind = {
            "_0": {"name": "No Gi", "bool": False},
            "id": "994FAC7F-FA9D-4B5E-9896-F72165F72A6C",
            "group": "Info",
        }
        self.metric_not_recorded = {
            "kind": {"bool": {"_0": {"name": "No Gi", "bool": False}}},
            "id": "994FAC7F-FA9D-4B5E-9896-F72165F72A6C",
            "group": "Info",
            "recorded": False,
        }

    def test_parse_metric_value(self):
        name, kind, value = conv.parse_metric_value(self.metric_data)
        self.assertEqual(name, "No Gi")
        self.assertEqual(kind, "bool")
        self.assertEqual(value, False)

    def test_parse_metric_no_kind(self):
        with self.assertRaises(KeyError):
            conv.parse_metric_value(self.metric_no_kind)

    def test_parse_metric_not_recorded(self):
        name, kind, value = conv.parse_metric_value(self.metric_not_recorded)
        self.assertEqual(name, "No Gi")
        self.assertEqual(kind, "bool")
        self.assertEqual(value, None)


class TestParsingOptions(unittest.TestCase):
    def setUp(self):
        """
        Create a test JSON which has three reflection instances: (not reverse chronological order in JSON)
        - one with metric "Perplexed"
        - new metric "Elated" is added, "Perplexed" is present but not recorded
        - "Perplexed" is removed, only "Elated" remains
        """
        self.json_string = """
        [
            {
                "id": "test_id_3",
                "notes": "",
                "name": "Mood",
                "metrics": [
                    {
                        "group": "",
                        "id": "metric_id_4",
                        "kind": {
                            "rating": {
                                "_0": {
                                    "name": "Elated",
                                    "score": 4
                                }
                            }
                        },
                        "recorded": true
                    }
                ],
                "date": 707233858.41729798
            },
            {
                "id": "test_id_2",
                "notes": "",
                "name": "Mood",
                "metrics": [
                    {
                        "group": "",
                        "id": "metric_id_3",
                        "kind": {
                            "rating": {
                                "_0": {
                                    "name": "Perplexed"
                                }
                            }
                        },
                        "recorded": false
                    },
                    {
                        "group": "",
                        "id": "metric_id_2",
                        "kind": {
                            "rating": {
                                "_0": {
                                    "name": "Elated",
                                    "score": 4
                                }
                            }
                        },
                        "recorded": true
                    }
                ],
                "date": 707233859.41729797
            },
            {
                "id": "test_id_1",
                "notes": "",
                "name": "Mood",
                "metrics": [
                    {
                        "group": "",
                        "id": "metric_id_1",
                        "kind": {
                            "rating": {
                                "_0": {
                                    "name": "Perplexed",
                                    "score": 3
                                }
                            }
                        },
                        "recorded": true
                    }
                ],
                "date": 707233860.41729796
            }
        ]
        """
        timestamp_1 = 707233858.41729798 + 978307200
        timestamp_2 = 707233859.41729797 + 978307200
        timestamp_3 = 707233860.41729796 + 978307200
        local_tz = tz.tzlocal()
        self.default_parsing_options = conv.ParsingOptions()
        self.expected_df_default = pd.DataFrame(
            {
                "Perplexed": [3.0, 0.0, np.nan],
                "Elated": [np.nan, 4, 4],
                "Timestamp": [timestamp_3, timestamp_2, timestamp_1],
                "Date": [
                    datetime.fromtimestamp(timestamp_3)
                    .astimezone(local_tz)
                    .strftime("%Y-%m-%d %H:%M:%S"),
                    datetime.fromtimestamp(timestamp_2)
                    .astimezone(local_tz)
                    .strftime("%Y-%m-%d %H:%M:%S"),
                    datetime.fromtimestamp(timestamp_1)
                    .astimezone(local_tz)
                    .strftime("%Y-%m-%d %H:%M:%S"),
                ],
                "ID": ["test_id_1", "test_id_2", "test_id_3"],
                "Notes": ["", "", ""],
            }
        )

        # self.expected_df_default = self.expected_df_default.set_index(
        #     "Timestamp"
        # ).sort_index()

        self.custom_parsing_options = conv.ParsingOptions()
        # define some custom parsing options
        self.custom_parsing_options.defaults["rating"] = 42
        self.custom_parsing_options.pre_metric_defaults["rating"] = 0
        self.custom_parsing_options.post_metric_defaults["rating"] = 1

        self.expected_df_custom = pd.DataFrame(
            {
                "Perplexed": [3, 42, 1],
                "Elated": [0, 4, 4],
                "Timestamp": [timestamp_3, timestamp_2, timestamp_1],
                "Date": [
                    datetime.fromtimestamp(timestamp_3)
                    .astimezone(local_tz)
                    .strftime("%Y-%m-%d %H:%M:%S"),
                    datetime.fromtimestamp(timestamp_2)
                    .astimezone(local_tz)
                    .strftime("%Y-%m-%d %H:%M:%S"),
                    datetime.fromtimestamp(timestamp_1)
                    .astimezone(local_tz)
                    .strftime("%Y-%m-%d %H:%M:%S"),
                ],
                "ID": ["test_id_1", "test_id_2", "test_id_3"],
                "Notes": ["", "", ""],
            }
        )


        # self.expected_df_custom = self.expected_df_custom.set_index(
        #     "Timestamp"
        # ).sort_index()

    def test_parse_json_parsing_options(self):
        """Compare default and custom parsing options output."""
        reflections_map_default = conv.parse_json(
            self.json_string, self.default_parsing_options
        )
        reflections_map_custom = conv.parse_json(
            self.json_string, self.custom_parsing_options
        )

        actual_df_default = reflections_map_default["Mood"]
        actual_df_custom = reflections_map_custom["Mood"]
        print("default parsing options:")
        print(f"expected:\n{self.expected_df_default}")
        print(f"actual:\n{actual_df_default}")

        assert_frame_equal(
            actual_df_default, self.expected_df_default, check_like=True
        )

        print("custom parsing options:")
        print(f"expected:\n{self.expected_df_custom}")
        print(f"actual:\n{actual_df_custom}")
        assert_frame_equal(
            actual_df_custom, self.expected_df_custom, check_like=True
        )


class TestJsonToCsvParsing(unittest.TestCase):
    def setUp(self):
        self.json_string = """
        [
            {
                "id": "test_id_1",
                "notes": "reflection_note_1",
                "name": "reflection_name_1",
                "metrics": [
                    {
                        "group": "",
                        "id": "metric_id",
                        "kind": {
                            "string": {
                                "_0": {
                                    "name": "string_metric",
                                    "string": "test_string"
                                }
                            }
                        },
                        "recorded": true
                    },
                    {
                        "group": "",
                        "id": "metric_id_2",
                        "kind": {
                            "choice": {
                                "_0": {
                                    "name": "choice_metric",
                                    "value": [
                                        "choice1",
                                        "choice2"
                                    ],
                                    "choice": "choice1"
                                }
                            }
                        },
                        "recorded": true
                    },
                    {
                        "group": "",
                        "id": "metric_id_3",
                        "kind": {
                            "bool": {
                                "_0": {
                                    "name": "bool_metric",
                                    "bool": true
                                }
                            }
                        },
                        "recorded": true
                    },
                    {
                        "group": "",
                        "id": "metric_id_4",
                        "kind": {
                            "unit": {
                                "_0": {
                                    "name": "unit_metric",
                                    "value": 15,
                                    "unit": "min"
                                }
                            }
                        },
                        "recorded": true
                    },
                    {
                        "group": "",
                        "id": "metric_id_5",
                        "kind": {
                            "rating": {
                                "_0": {
                                    "name": "rating_metric",
                                    "score": 5
                                }
                            }
                        },
                        "recorded": true
                    }
                ],
                "date": 707233858.41729798
            },
            {
                "id": "test_id_2",
                "notes": "reflection_note_2",
                "name": "reflection_name_2",
                "metrics": [
                    {
                        "group": "",
                        "id": "metric_id_6",
                        "kind": {
                            "string": {
                                "_0": {
                                    "name": "string_metric_2",
                                    "string": "test_string_3"
                                }
                            }
                        },
                        "recorded": true
                    },
                    {
                        "group": "",
                        "id": "metric_id_7",
                        "kind": {
                            "scalar": {
                                "_0": {
                                    "name": "scalar_metric",
                                    "scalar": 0
                                }
                            }
                        },
                        "recorded": true
                    }
                ],
                "date": 707233859.41729797
            },
            {
                "id": "test_id_3",
                "notes": "reflection_note_3",
                "name": "reflection_name_2",
                "metrics": [
                    {
                        "group": "",
                        "id": "metric_id_8",
                        "kind": {
                            "string": {
                                "_0": {
                                    "name": "string_metric_2",
                                    "string": "test_string_2"
                                }
                            }
                        },
                        "recorded": true
                    },
                    {
                        "group": "",
                        "id": "metric_id_9",
                        "kind": {
                            "scalar": {
                                "_0": {
                                    "name": "scalar_metric",
                                    "scalar": 2
                                }
                            }
                        },
                        "recorded": true
                    }
                ],
                "date": 707233860.41729796
            }
        ]
        """
        timestamp_1 = 707233858.41729798 + 978307200
        timestamp_2 = 707233859.41729797 + 978307200
        timestamp_3 = 707233860.41729796 + 978307200
        local_tz = tz.tzlocal()
        self.expected_df_1 = pd.DataFrame(
            {
                "string_metric": ["test_string"],
                "choice_metric": ["choice1"],
                "bool_metric": [True],
                "unit_metric": [
                    15
                ],  # the unit ("min") is not currently considered in parsing, only the value
                "rating_metric": [5],
                "Timestamp": [timestamp_1],
                "Date": [
                    datetime.fromtimestamp(timestamp_1)
                    .astimezone(local_tz)
                    .strftime("%Y-%m-%d %H:%M:%S")
                ],
                "ID": ["test_id_1"],
                "Notes": ["reflection_note_1"],
            }
        )

        self.expected_df_2 = pd.DataFrame(
            {
                "string_metric_2": ["test_string_3", "test_string_2"],
                "scalar_metric": [0, 2],
                "Timestamp": [timestamp_2, timestamp_3],
                "Date": [
                    datetime.fromtimestamp(timestamp_2)
                    .astimezone(local_tz)
                    .strftime("%Y-%m-%d %H:%M:%S"),
                    datetime.fromtimestamp(timestamp_3)
                    .astimezone(local_tz)
                    .strftime("%Y-%m-%d %H:%M:%S"),
                ],
                "ID": ["test_id_2", "test_id_3"],
                "Notes": ["reflection_note_2", "reflection_note_3"],
            }
        )
        
        self.parsing_options = conv.ParsingOptions()

    def test_parse_json(self):
        reflections_map = conv.parse_json(
            self.json_string, self.parsing_options
        )
        actual_df_1 = reflections_map["reflection_name_1"]
        actual_df_2 = reflections_map["reflection_name_2"]
        assert_frame_equal(actual_df_1, self.expected_df_1, check_like=True)

        print("expected")
        print(self.expected_df_2)
        print("actual")
        print(actual_df_2)
        assert_frame_equal(actual_df_2, self.expected_df_2, check_like=True)

    def test_save_dataframes_to_csv(self):
        reflections_map = {
            "reflection_name_1": self.expected_df_1,
            "reflection_name_2": self.expected_df_2,
        }
        conv.save_dataframes_to_csv(reflections_map, ".")
        self.assertTrue(os.path.exists("reflection_name_1.csv"))
        self.assertTrue(os.path.exists("reflection_name_2.csv"))

    def tearDown(self):
        if os.path.exists("reflection_name_1.csv"):
            os.remove("reflection_name_1.csv")
        if os.path.exists("reflection_name_2.csv"):
            os.remove("reflection_name_2.csv")


if __name__ == "__main__":
    unittest.main()
