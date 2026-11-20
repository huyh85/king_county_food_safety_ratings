"""
Tony Hang, Jaiden Poon, Amy Li
CSE 163 A

A file that contains CSE 163 Project Exploration
Data Testing for the King County's Public
Health Safety - Food Handling Certification
"""
import pandas as pd
from data_cleanup import clean_inspections


def test_clean_inspections():
    """
    Tests that inspection data is filtered and grouped correctly.
    """
    # Create a small dataset with known results
    test_data = pd.DataFrame({
        "Name": ["Cafe A", "Cafe A", "Cafe B", "Cafe C",
                 "Cafe D", "Cafe E"],
        "Business_ID": ["A", "A", "B", "C", "D", "E"],
        "Inspection_Serial_Num": ["1", "1", "2", "3", "4", "5"],
        "Inspection Date": ["01/15/2023", "01/15/2023",
                            "06/20/2024", "03/02/2025",
                            "04/10/2026", "05/01/2024"],
        "Inspection Type": ["Routine Inspection/Field Review",
                            "Routine Inspection/Field Review",
                            "Routine Inspection/Field Review",
                            "Routine Inspection/Field Review",
                            "Routine Inspection/Field Review",
                            "Educational Inspection"],
        "Zip Code": ["98105-1234", "98105-1234", "98103",
                     "98101", "98122", "98105"],
        "Inspection Score": [15, 15, 5, 0, 10, 0],
        "Violation Type": ["RED", "BLUE", "BLUE", None,
                           "RED", None]
    })

    cleaned = clean_inspections(test_data)

    # Check that four inspections remain
    assert len(cleaned) == 4

    # Check that inspections are not duplicated
    assert cleaned["Inspection_Serial_Num"].is_unique

    # Check that ZIP codes have five digits
    assert (cleaned["Zip Code"].str.len() == 5).all()

    # Check that violation categories were assigned correctly
    assert cleaned["Type of Violation"].tolist() == [
        "RED", "BLUE", "ZERO", "RED"
    ]

    # Check that Has Violation is correct
    assert cleaned["Has Violation"].tolist() == [
        True, True, False, True
    ]

    print("All cleaning tests passed!")


if __name__ == "__main__":
    test_clean_inspections()
