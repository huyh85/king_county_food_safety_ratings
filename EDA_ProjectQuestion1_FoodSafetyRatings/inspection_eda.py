"""
Tony Hang, Jaiden Poon, Amy Li
CSE 163 A

A file that contains CSE 163 Project Exploration
Data Inspection for the King County's Public
Health Safety - Food Handling Certification
"""
import pandas as pd


def main():
    inspections = pd.read_csv("food_inspections.csv")

    # Examine the dataset's structure
    print("Dataset dimensions:")
    print(inspections.shape)

    print("Column names:")
    print(inspections.columns.tolist())

    print("First five rows:")
    print(inspections.head())

    # Identify missing values
    print("Missing values by column:")
    print(inspections.isna().sum())

    # Explore important categorical variables
    print("Inspection types:")
    print(inspections["Inspection Type"].value_counts())

    print("Violation types:")
    print(inspections["Violation Type"].value_counts(
        dropna=False
    ))

    print("Inspections by ZIP code:")
    print(inspections["Zip Code"].value_counts())


if __name__ == "__main__":
    main()
