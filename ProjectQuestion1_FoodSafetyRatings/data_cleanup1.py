
import pandas as pd
import matplotlib.pyplot as plt


def plot_inspection_scores(inspections, top_zips):
    """
    Plots the average inspection score for the five ZIP codes
    with the most inspections from 2021 to 2025.
    """
    plt.figure()

    for zip_code in top_zips:
        # Get inspections for this ZIP code
        zip_data = inspections[inspections["Zip Code"] == zip_code]

        # Calculate average score for each year
        avg_scores = zip_data.groupby("Year")["Inspection Score"].mean()

        # Plot a line for this ZIP code
        plt.plot(avg_scores.index, avg_scores.values,
                 marker="o", label=zip_code)

    plt.title("Average Violation Score by ZIP Code (2021-2025)")
    plt.xlabel("Year")
    plt.ylabel("Average Violation Score")
    plt.xticks([2021, 2022, 2023, 2024, 2025])
    plt.legend(title="ZIP Code")
    plt.tight_layout()
    return plt.gcf()


def plot_red_violations(inspections, top_zips):
    """
    Plots the percentage of inspections with RED violations
    for the five ZIP codes with the most inspections.
    """
    plt.figure()

    for zip_code in top_zips:
        # Get inspections for this ZIP code
        zip_data = inspections[inspections["Zip Code"] == zip_code].copy()

        # Check which inspections have RED violations
        zip_data["Red Violation"] = (zip_data["Type of Violation"] == "RED")

        # Calculate percentage of RED violations each year
        red_rates = zip_data.groupby("Year")["Red Violation"].mean() * 100

        # Plot a line for this ZIP code
        plt.plot(red_rates.index, red_rates.values,
                 marker="o", label=zip_code)

    plt.title("Critical Violation Rate by ZIP Code (2021-2025)")
    plt.xlabel("Year")
    plt.ylabel("Inspections with RED Violations (%)")
    plt.xticks([2021, 2022, 2023, 2024, 2025])
    plt.legend(title="ZIP Code")
    plt.tight_layout()
    return plt.gcf()


def main():
    inspections = pd.read_csv("cleaned_inspections.csv")

    # Get the year from the inspection date
    inspections["Inspection Date"] = pd.to_datetime(inspections["Inspection Date"])
    inspections["Year"] = inspections["Inspection Date"].dt.year

    # Count how many inspections each ZIP code has
    zip_counts = inspections["Zip Code"].value_counts()

    # Find the five ZIP codes with the most inspections
    zip1 = zip_counts.idxmax()
    zip_counts = zip_counts.drop(zip1)

    zip2 = zip_counts.idxmax()
    zip_counts = zip_counts.drop(zip2)

    zip3 = zip_counts.idxmax()
    zip_counts = zip_counts.drop(zip3)

    zip4 = zip_counts.idxmax()
    zip_counts = zip_counts.drop(zip4)

    zip5 = zip_counts.idxmax()

    top_zips = [zip1, zip2, zip3, zip4, zip5]
    print("Top five ZIP codes:", top_zips)

    # Create both graphs
    fig1 = plot_inspection_scores(inspections, top_zips)
    fig2 = plot_red_violations(inspections, top_zips)

    # Save figures
    fig1.savefig("inspection_scores.png")
    fig2.savefig("red_violation_rates.png")


if __name__ == "__main__":
    main()
