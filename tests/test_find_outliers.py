import unittest
import pandas as pd
import numpy as np
from reflect import utils as utils


class TestFindOutliers(unittest.TestCase):
    def setUp(self):
        """Create some test data for the tests"""
        date_range = pd.date_range(start="1/1/2020", end="1/31/2020")
        np.random.seed(0)
        data = np.random.randint(3, 5, size=(len(date_range), 3))
        self.df = pd.DataFrame(data, columns=['Elated', 'Meh', 'Shocked'])
        self.df['Date'] = date_range
        self.df.set_index('Date', inplace=True)

    def test_no_outliers(self):
        """Test that function returns a dataframe of all NaNs when there are no 
        outliers
        """
        df_outliers = utils.find_outliers(self.df, "3D")
        self.assertTrue(df_outliers.isna().all().all())

    def test_outliers_identified(self):
        """Test that function correctly identifies outliers"""
        # Introduce an outlier
        self.df.loc["2020-01-15", "Elated"] = 0
        df_outliers = utils.find_outliers(self.df, "7D")
        self.assertEqual(df_outliers.loc["2020-01-15", "Elated"], 0)

    def test_center_argument(self):
        """Test the effect of the center argument"""

        # Set everything after 2020-01-15 to zero which introduces a stepwise 
        # change in the data
        self.df.loc["2020-01-15":, "Elated"] = 0  
        # Without centering
        df_outliers_no_center = utils.find_outliers(
            self.df, "7D", center=False
        )
        # With centering
        df_outliers_center = utils.find_outliers(self.df, "7D", center=True)

        # Expect that 2020-01-15 will be treated as an outlier when considering 
        # the window of the week up to that data point
        self.assertEqual(df_outliers_no_center.loc["2020-01-15", "Elated"], 0)
        # If the outlier detection is forward looking, it is not treated as an 
        # outlier, as the following values in the dataset are all zero
        self.assertNotIn("Elated", df_outliers_center.columns)



    def test_time_window(self):
        """Test the effect of the time window"""
        # Introduce an outlier
        self.df.loc["2020-01-15", "Elated"] = 0
        # Smaller time window
        df_outliers_small_window = utils.find_outliers(self.df, "7D")
        # Larger time window
        df_outliers_large_window = utils.find_outliers(self.df, "14D")
        # This is a significant outlier and should be picked up in both cases
        self.assertEqual(
            df_outliers_small_window.loc["2020-01-15", "Elated"],
            df_outliers_large_window.loc["2020-01-15", "Elated"],
        )


if __name__ == "__main__":
    unittest.main()
