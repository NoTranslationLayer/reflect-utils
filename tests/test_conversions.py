import unittest
import os
import pandas as pd
from pandas.testing import assert_frame_equal

# Assuming the functions are defined here
# import your_module_name 

class TestParsingFunctions(unittest.TestCase):
    def setUp(self):
        self.json_string = """
        [
            {
                "id": "test_id",
                "notes": "test_note",
                "name": "test_name",
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
                        "id": "metric_id",
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
                        "id": "metric_id",
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
                        "id": "metric_id",
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
                        "id": "metric_id",
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
            }
        ]
        """
        self.expected_df = pd.DataFrame({
            'string_metric': ['test_string'],
            'choice_metric': ['choice1'],
            'bool_metric': [True],
            'unit_metric': [15],  # the unit ("min") is not currently considered in parsing, only the value
            'rating_metric': [5],
            'date': [707233858.41729796],
            'id': ['test_id'],
            'notes': ['test_note']
        })

    def test_parse_json(self):
        reflections_map = your_module_name.parse_json(self.json_string)
        actual_df = reflections_map['test_name']
        assert_frame_equal(actual_df, self.expected_df)

    def test_save_dataframes_to_csv(self):
        reflections_map = {'test_name': self.expected_df}
        your_module_name.save_dataframes_to_csv(reflections_map, '.')
        self.assertTrue(os.path.exists('test_name.csv'))

    def tearDown(self):
        if os.path.exists('test_name.csv'):
            os.remove('test_name.csv')

if __name__ == '__main__':
    unittest.main()
