import unittest
import os
import pandas as pd
import numpy as np
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
        Create a test JSON which has three reflection instances: (not reverse 
        chronological order in JSON)
        - one with metric "Perplexed"
        - new metric "Elated" is added, "Perplexed" is present but not recorded
        - "Perplexed" is removed, only "Elated" remains
        """
        self.json_string = """
        [
            {
                "id": "id3",
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
                "date": 707954444.948071
            },
            {
                "id": "id2",
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
                "date": 705867495.55896401
            },
            {
                "id": "id1",
                "notes": "",
                "name": "Mood",
                "metrics": [
                    {
                        "group": "",
                        "id": "metric_id1",
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
                "date": 702429159.13179898
            }
        ]
        """
        ts3 = 707954444.948071
        ts2 = 705867495.55896401
        ts1 = 702429159.13179898
        self.default_parsing_options = conv.ParsingOptions()
        self.expected_df_default = pd.DataFrame(
            {
                "Perplexed": [3.0, 0.0, np.nan],
                "Elated": [np.nan, 4, 4],
                "Timestamp": [ts1, ts2, ts3],
                "Date": [
                    conv.convert_timestamp(ts1),
                    conv.convert_timestamp(ts2),
                    conv.convert_timestamp(ts3),
                ],
                "ID": ["id1", "id2", "id3"],
                "Notes": ["", "", ""],
            }
        )

        self.custom_parsing_options = conv.ParsingOptions()
        # define some custom parsing options
        self.custom_parsing_options.defaults["rating"] = 42
        self.custom_parsing_options.pre_metric_defaults["rating"] = 0
        self.custom_parsing_options.post_metric_defaults["rating"] = 1

        self.expected_df_custom = pd.DataFrame(
            {
                "Perplexed": [3, 42, 1],
                "Elated": [0, 4, 4],
                "Timestamp": [ts1, ts2, ts3],
                "Date": [
                    conv.convert_timestamp(ts1),
                    conv.convert_timestamp(ts2),
                    conv.convert_timestamp(ts3),
                ],
                "ID": ["id1", "id2", "id3"],
                "Notes": ["", "", ""],
            }
        )

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
                "id": "id1",
                "notes": "Note 3",
                "name": "Reflection2",
                "metrics": [
                    {
                        "group": "",
                        "id": "metric_id",
                        "kind": {
                            "string": {
                                "_0": {
                                    "name": "String Metric 3",
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
                                    "name": "Choice Metric",
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
                                    "name": "Bool Metric",
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
                                    "name": "Unit Metric",
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
                                    "name": "Rating Metric",
                                    "score": 5
                                }
                            }
                        },
                        "recorded": true
                    }
                ],
                "date": 707954444.948071
            },
            {
                "id": "id2",
                "notes": "Note 2",
                "name": "Reflection1",
                "metrics": [
                    {
                        "group": "",
                        "id": "metric_id_6",
                        "kind": {
                            "string": {
                                "_0": {
                                    "name": "String Metric 1",
                                    "string": "string_2"
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
                                    "name": "Scalar Metric 1",
                                    "scalar": 0
                                }
                            }
                        },
                        "recorded": true
                    }
                ],
                "date": 705867495.55896401
            },
            {
                "id": "id3",
                "notes": "Note 1",
                "name": "Reflection1",
                "metrics": [
                    {
                        "group": "",
                        "id": "metric_id_8",
                        "kind": {
                            "string": {
                                "_0": {
                                    "name": "String Metric 1",
                                    "string": "string_1"
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
                                    "name": "Scalar Metric 1",
                                    "scalar": 2
                                }
                            }
                        },
                        "recorded": true
                    }
                ],
                "date": 702429159.13179898
            }
        ]
        """
        ts3 = 707954444.948071
        ts2 = 705867495.55896401
        ts1 = 702429159.13179898
        self.expected_df_1 = pd.DataFrame(
            {
                "String Metric 3": ["test_string"],
                "Choice Metric": ["choice1"],
                "Bool Metric": [True],
                "Unit Metric": [
                    15
                ],  # the unit ("min") is not currently considered in parsing, only the value
                "Rating Metric": [5],
                "Timestamp": [ts3],
                "Date": [
                    conv.convert_timestamp(ts3),
                ],
                "ID": ["id1"],
                "Notes": ["Note 3"],
            }
        )

        self.expected_df_2 = pd.DataFrame(
            {
                "String Metric 1": ["string_1", "string_2"],
                "Scalar Metric 1": [2, 0],
                "Timestamp": [ts1, ts2],
                "Date": [
                    conv.convert_timestamp(ts1),
                    conv.convert_timestamp(ts2),
                ],
                "ID": ["id3", "id2"],
                "Notes": ["Note 1", "Note 2"],
            }
        )

        self.parsing_options = conv.ParsingOptions()

    def test_parse_json(self):
        reflections_map = conv.parse_json(
            self.json_string, self.parsing_options
        )
        actual_df_1 = reflections_map["Reflection2"]
        actual_df_2 = reflections_map["Reflection1"]
        assert_frame_equal(actual_df_1, self.expected_df_1, check_like=True)

        print("expected")
        print(self.expected_df_2)
        print("actual")
        print(actual_df_2)
        assert_frame_equal(actual_df_2, self.expected_df_2, check_like=True)

    def test_save_dataframes_to_csv(self):
        reflections_map = {
            "Reflection2": self.expected_df_1,
            "Reflection1": self.expected_df_2,
        }
        conv.save_dataframes_to_csv(reflections_map, ".")
        self.assertTrue(os.path.exists("Reflection2.csv"))
        self.assertTrue(os.path.exists("Reflection1.csv"))

    def tearDown(self):
        if os.path.exists("Reflection2.csv"):
            os.remove("Reflection2.csv")
        if os.path.exists("Reflection1.csv"):
            os.remove("Reflection1.csv")


if __name__ == "__main__":
    unittest.main()
