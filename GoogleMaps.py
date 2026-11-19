"""
Tony Hang, Jaiden Poon, Amy Li
CSE 163 A

A file that contains CSE 163 Project Exploration
Data Analysis for the Google Maps - Public Review
Dataset
"""

# Libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Data Cleaning and Merging
def food_handling(misc):
    """
    Checking if the rows is a restaurant or not,
    by checking if the business entity have dine-in
    or take out options
    """
    if not isinstance(misc, dict):
        return False
    if 'Dining options' in misc:
        return True
    service = misc.get('Service options', [])
    return 'Dine-in' in service or 'Takeout' in service

def business_reviews(path):
    """
    Loading the Google Business Review data
    and remove duplicates, data does not
    have a value in address or average ratings
    columns. Creating ZIPCODE from the full address
    line. And Groupping average ratings the data by Zipcode
    """
    df = pd.read_json(path, lines = True)

    # Drop any duplicate values
    df = df.drop_duplicates(subset='gmap_id')

    # Keep business that is a business that need a food
    # handling license
    df = df[df['MISC'].apply(food_handling)]

    # Drop business that does not have a rating or address
    df = df.dropna(subset=['avg_rating', 'address']).copy()

    # Seperate the zipcode from address line
    df['zipcode'] = df['address'].str[-5:]
    df = df[df['zipcode'].str.isdigit()]

    # Group by the Business Review data by Zipcode
    df_zip = df.groupby('zipcode').agg(
        business_avg_rating=('avg_rating','mean')
    )
    return df_zip

def food_inspections(path):
    """
    Loading King County Public Health Safety Food
    Inspection Ratings Data. The data being loaded
    has been cleaned and exported to csv file from EDA 1
    """
    kc = pd.read_csv(path, dtype={'Zip Code': str,
                                 'Parcel Number': str})

    ## Returning one row per business
    business = kc.groupby(['Business_ID', 'Zip Code']).agg(
        avg_score=('Inspection Score', 'mean'),
    ).reset_index()

    business_zip = business.groupby('Zip Code').agg(
        kc_business =('avg_score', 'size'),
        kc_avg_score=('avg_score', 'mean'),
        kc_median_score=('avg_score', 'median')
    )
    return business_zip

def merge_zip(business_reviews_zip, business_zip):
    """
    Merge the summaries on Zipcode and Return only on the
    Zip code that found on both.
    """
    merged = business_reviews_zip.join(business_zip, how='inner')
    return merged.reset_index().round(2)

def explore_merged(merged, path):
    """
    Explore the data, after merging
    """
    merged.to_csv(path, index=False)

    print('Rows, columns: ' + str(merged.shape))
    print(merged.dtypes)

    print('\nMissing values per column:')
    print(merged.isna().sum())
    print('Rows with any missing value: '
          + str(merged.isna().any(axis=1).sum()))

    print('\nSeven-number summary:')
    cols = ['business_avg_rating', 'kc_avg_score',
            'kc_median_score', 'kc_business']
    print(merged[cols].describe().drop('count').round(2))

    zip_counts = merged['zipcode'].value_counts().sort_index()
    print('\nUnique ZIP codes: ' + str(zip_counts.size))
    print(zip_counts.to_string())


# Visualization

def scatter_plot(merged):
    """
    Scatter plot of each Zipcode average inspection score against
    the Google rating, including a tendline.
    """
    x = merged['kc_avg_score']
    y = merged['business_avg_rating']

    # Fit line
    slope, intercept = np.polyfit(x,y,1)
    x_line = np.sort(x)
    plt.figure(figsize=(9, 6))

    plt.scatter(x, y, s=merged['kc_business'], alpha=0.5)
    plt.plot(x_line, slope * x_line + intercept, color='red')

    plt.xlabel('Average Inspection Score')
    plt.ylabel('Google Average Ratings')
    plt.title('Google Ratings vs Inspection Score by Zipcode')

    plt.savefig('score_ratings.png')

def rank_plot(merged):
    plt.figure(figsize=(9, 6))
    plt.scatter(merged['kc_avg_score'].rank(),
                merged['business_avg_rating'].rank())
    plt.xlabel('Rank by inspection score (1 = fewest violations)')
    plt.ylabel('Rank by Google rating (1 = lowest rated)')
    plt.title('ZIP rankings: inspections vs. Google')
    plt.savefig('rank.png')

def mean_median(merged):
    plt.figure(figsize=(9, 6))
    plt.scatter(merged['kc_median_score'], merged['kc_avg_score'])
    lim = [0, merged[['kc_avg_score', 'kc_median_score']].max().max()]
    plt.plot(lim, lim, linestyle='--')
    plt.xlabel('Median inspection score')
    plt.ylabel('Mean inspection score')
    plt.title('Are a few businesses skewing ZIP averages?')
    plt.savefig('mean.png')


def main():
    business_reviews_zip = business_reviews('meta-Washington.json')
    business_zip = food_inspections('kc_inspections.csv')
    merged = merge_zip(business_reviews_zip, business_zip)
    explore_merged(merged, 'merged_zip.csv')
    
    scatter_plot(merged)
    rank_plot(merged)
    mean_median(merged)

if __name__ == '__main__':
    main()