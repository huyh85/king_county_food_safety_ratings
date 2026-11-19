import pandas as pd

"""
Data Cleanup to align with research question and reduce noise
    Out of range dates --> Keep 2021–2025
    Multiple inspection types --> Keep Routine Inspection/Field Review
    ZIP codes have inconsistent formats --> Standardize to five digits
    Multiple rows per inspection --> Group using Inspection_Serial_Num
    41,703 missing Violation Type values --> Keep them where they indicate no violation
    Remove missing inspection score restraunts
    Mixed Parcel Number types --> Read as strings
"""
def clean_inspections(inspection):
    data = inspection.copy()
        # Keep only routine inspections
    data = data[data["Inspection Type"] == "Routine Inspection/Field Review"].copy()

        # Standardize ZIP codes to five digits
    data["Zip Code"] = data["Zip Code"].str[:5]

        # Remove inspections with missing scores
    data = data.dropna(subset=["Inspection Score"])

            # Identify inspections with violations
    data["Has Violation"] = data["Violation Type"].notna()

    # Assign numerical values to violation types
    data["Violation Level"] = data["Violation Type"].map({
        "RED": 2,
        "BLUE": 1
    }).fillna(0)

    # Combine multiple rows belonging to the same inspection
    data = data.groupby("Inspection_Serial_Num", as_index=False).agg({
        "Name": "first",
        "Business_ID": "first",
        "Inspection Date": "first",
        "Zip Code": "first",
        "Inspection Score": "first",
        "Has Violation": "max",
        "Violation Level": "max"
    })

    # Convert violation levels back to categories
    data["Type of Violation"] = data["Violation Level"].map({
        2: "RED",
        1: "BLUE",
        0: "ZERO"
    })

    # Remove temporary numerical column
    data = data.drop(columns=["Violation Level"])

    return data


def main():
    inspections = pd.read_csv("food_inspections.csv")
    cleaned_data = clean_inspections(inspections)

    print("Original dataset:", inspections.shape)
    print("Cleaned dataset:", cleaned_data.shape)
    print(cleaned_data.head())

    cleaned_data.to_csv("cleaned_inspections.csv", index=False)


if __name__ == "__main__":
    main()