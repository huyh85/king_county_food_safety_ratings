"""
Tony Hang, Jaiden Poon, Amy Li
CSE 163 A

A file that contains CSE 163 Project Exploration
Data Analysis for the Google Maps - Public Review
Dataset Test File
"""

# Libraries
import pandas as pd
from GoogleMaps import (food_handling, merge_zip)


# Data Cleaning and Merging
def test_food_handling():
    """
    Test food business are correctly identified
    missing values are removed
    """
    # Food Business are correctly identify
    assert food_handling({'Dining options': ['Dine-in']})

    # Business that are not operating with food
    assert not food_handling({'Service options:': ['Grocery']})

    # Missing values
    assert not food_handling(None)


def test_merge_zip():
    """
    Test that merge Zip code found in both dataset are being keep
    """
    reviews = pd.DataFrame({
        'zipcode': ['98105', '98101'],
        'business_avg_rating' : [4.5, 3.0]
    }).set_index('zipcode')

    inspections = pd.DataFrame({
        'Zip Code': ['98105', '98101'],
        'kc_business': [3, 1],
        'kc_avg_score': [8.333, 5.0],
        'kc_median_score': [5.0, 5.0]
    }).set_index('Zip Code')

    merged = merge_zip(reviews, inspections)

    row = merged[merged['zipcode'] == '98105']
    assert row['kc_avg_score'].tolist() == [8.33]


def main():
    test_food_handling()
    test_merge_zip()

    print('All test passed')


if __name__ == '__main__':
    main()