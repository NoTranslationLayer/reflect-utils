import unittest
import os
import pandas as pd
from datetime import datetime
from dateutil import tz
from pandas.testing import assert_frame_equal

from reflect import conversions as conv

class TestParsingFunctions(unittest.TestCase):
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
                "date": 707233858.41729796
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
                                    "string": "test_string_2"
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
                        "id": "metric_id_7",
                        "kind": {
                            "string": {
                                "_0": {
                                    "name": "string_metric_2",
                                    "string": "test_string_3"
                                }
                            }
                        },
                        "recorded": true
                    }
                ],
                "date": 707233860.41729798
            }
        ]
        """
        timestamp_1 = 707233858.41729796
        timestamp_2 = 707233859.41729797
        timestamp_3 = 707233860.41729798
        local_tz = tz.tzlocal()
        self.expected_df_1 = pd.DataFrame({
            'string_metric': ['test_string'],
            'choice_metric': ['choice1'],
            'bool_metric': [True],
            'unit_metric': [15],   # the unit ("min") is not currently considered in parsing, only the value
            'rating_metric': [5],
            'Timestamp': [timestamp_1],
            'Date': [datetime.fromtimestamp(timestamp_1).astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S")],
            'ID': ['test_id_1'],
            'Notes': ['reflection_note_1']
        })

        self.expected_df_2 = pd.DataFrame({
            'string_metric_2': ['test_string_2', 'test_string_3'],
            'Timestamp': [timestamp_2, timestamp_3],
            'Date': [datetime.fromtimestamp(timestamp_2).astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S"),
                     datetime.fromtimestamp(timestamp_3).astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S")],
            'ID': ['test_id_2', 'test_id_3'],
            'Notes': ['reflection_note_2', 'reflection_note_3']
        })

    def test_parse_json(self):
        reflections_map = conv.parse_json(self.json_string)
        actual_df_1 = reflections_map['reflection_name_1']
        actual_df_2 = reflections_map['reflection_name_2']
        assert_frame_equal(actual_df_1, self.expected_df_1)

        print(actual_df_2)
        print(self.expected_df_2)
        assert_frame_equal(actual_df_2, self.expected_df_2)

    def test_save_dataframes_to_csv(self):
        reflections_map = {'reflection_name_1': self.expected_df_1, 'reflection_name_2': self.expected_df_2}
        conv.save_dataframes_to_csv(reflections_map, '.')
        self.assertTrue(os.path.exists('reflection_name_1.csv'))
        self.assertTrue(os.path.exists('reflection_name_2.csv'))

    def tearDown(self):
        if os.path.exists('reflection_name_1.csv'):
            os.remove('reflection_name_1.csv')
        if os.path.exists('reflection_name_2.csv'):
            os.remove('reflection_name_2.csv')

if __name__ == '__main__':
    unittest.main()
