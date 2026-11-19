
import pandas as pd


"""
Provides a summary of the variables of interest for RQ1.
Quantitative variables use a seven-number summary.
Identifying variables unique for the restaurant use counts of unique
values alongside first five values. Categorical variables like Has
Violation and Type of Violation uses dictionary with key of potential
values and value of count of the key.

"""


def variable_summary(inspections):
    # Summarize restaurant names and identifiers
    for column in ["Name", "Business_ID", "Inspection_Serial_Num"]:
        print()
        print(column)
        print("Number of unique values:", inspections[column].nunique())
        print("First five values:", inspections[column].unique()[:5])

    # Summarize inspection dates
    print()
    print("Inspection Date:")
    dates = pd.to_datetime(inspections["Inspection Date"])
    print("Number of unique dates:", dates.nunique())
    print("Earliest date:", dates.min())
    print("Latest date:", dates.max())

    # Summarize ZIP codes
    print()
    print("Zip Code:")
    print("Number of unique ZIP codes:", inspections["Zip Code"].nunique())
    print(inspections["Zip Code"].value_counts().to_dict())

    # Seven-number summary for inspection scores
    print()
    print("Inspection Score:")
    print(inspections["Inspection Score"].describe().drop("count"))

    # Summarize whether inspections had violations
    print()
    print("Has Violation:")
    print(inspections["Has Violation"].value_counts().to_dict())

    # Summarize violation types
    print()
    print("Type of Violation:")
    print(inspections["Type of Violation"].value_counts().to_dict())


def main():
    inspections = pd.read_csv(
        "cleaned_inspections.csv")
    variable_summary(inspections)


if __name__ == "__main__":
    main()
