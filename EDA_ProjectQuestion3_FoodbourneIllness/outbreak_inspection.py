"""Collect King County foodborne outbreak data and analyze inspections."""

from pathlib import Path
import string
from urllib.parse import urljoin

import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns
from bs4 import BeautifulSoup


BASE_URL = (
    "https://kingcounty.gov/en/dept/dph/health-safety/"
    "disease-illness/foodborne-illness-outbreaks"
)
HEADERS = {"User-Agent": "Mozilla/5.0"}
DETAIL_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE_URL,
}
INSPECTION_FILE = "Food_Establishment_Inspection_Data_20261117.csv"


def clean_address(address):
    """Standardize an address for matching."""
    if pd.isna(address):
        return ""

    address = str(address).upper()
    address = address.translate(
        str.maketrans("", "", string.punctuation)
    )
    return " ".join(address.split())


def scrape_outbreak_listing():
    """Scrape outbreak summaries and their detail-page URLs."""
    response = requests.get(
        BASE_URL, headers=HEADERS, timeout=30
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table")
    outbreak_records = []

    for table in tables[:3]:
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 4:
                continue

            link = cells[2].find("a", href=True)
            if link is None:
                continue

            outbreak_records.append({
                "date_posted": cells[0].get_text(" ", strip=True),
                "last_updated": cells[1].get_text(" ", strip=True),
                "food_business": cells[2].get_text(" ", strip=True),
                "suspected_organism": cells[3].get_text(" ", strip=True),
                "source_url": urljoin(BASE_URL, link["href"]),
            })

    outbreak_df = pd.DataFrame(outbreak_records)
    if outbreak_df.empty:
        raise ValueError(
            "No outbreak records were found on the listing page."
        )

    return outbreak_df


def scrape_outbreak_details(outbreak_df):
    """Visit outbreak detail pages and append their table information."""
    all_details = []

    for _, row in outbreak_df.iterrows():
        url = row["source_url"]

        try:
            response = requests.get(
                url, headers=DETAIL_HEADERS, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as error:
            print(f"Failed to scrape {url}: {error}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        details = {}

        if table:
            cells = table.find_all(["th", "td"])
            for index in range(1, len(cells) - 1, 2):
                label = cells[index].get_text(" ", strip=True)
                value = cells[index + 1].get_text(" ", strip=True)
                details[label] = value

        record = row.to_dict()
        record.update(details)
        all_details.append(record)

    if not all_details:
        raise ValueError(
            "No outbreak detail pages could be retrieved."
        )

    return pd.DataFrame(all_details)


def clean_outbreak_data(detailed_df):
    """Standardize outbreak detail fields and data types."""
    column_groups = {
        "cases": ["Cases"],
        "hospitalizations": ["Hospitalizations"],
        "deaths": ["Deaths"],
        "status": ["Status"],
        "location": ["Location"],
        "meal_date_range": [
            "Meal Date Range",
            "Meal Date",
            "Meal date",
            "Meal dates",
            "Meal date range",
        ],
        "illness_onset_date_range": [
            "Illness Onset Date Range",
            "Illness Onset Date",
            "Illness onset date range",
            "Illness onset date range:",
        ],
        "current_inspection_rating": [
            "Current Inspection Rating",
            "Current inspection rating",
        ],
        "date_suspected_products_were_purchased": [
            "Date suspected products were purchased:"
        ],
    }

    base_columns = [
        "date_posted",
        "last_updated",
        "food_business",
        "suspected_organism",
        "source_url",
    ]
    cleaned_df = detailed_df[base_columns].copy()

    for new_column, old_columns in column_groups.items():
        available_columns = [
            column for column in old_columns
            if column in detailed_df.columns
        ]

        if available_columns:
            cleaned_df[new_column] = (
                detailed_df[available_columns]
                .bfill(axis=1)
                .iloc[:, 0]
            )
        else:
            cleaned_df[new_column] = pd.NA

    for column in ["cases", "hospitalizations", "deaths"]:
        cleaned_df[column] = pd.to_numeric(
            cleaned_df[column], errors="coerce"
        )

    for column in ["date_posted", "last_updated"]:
        cleaned_df[column] = pd.to_datetime(
            cleaned_df[column],
            format="mixed",
            errors="coerce",
        )

    status_mapping = {
        "investigation is complete": "Completed",
        "investigation is completed": "Completed",
        "investigation in completed": "Completed",
        "investigation is ongoing": "Ongoing",
    }
    cleaned_df["status"] = (
        cleaned_df["status"]
        .astype("string")
        .str.strip()
        .str.lower()
        .map(status_mapping)
    )

    rating_mapping = {
        "good": "Good",
        "okay": "Okay",
        "needs to improve": "Needs to Improve",
        "excellent": "Excellent",
        "n/a": "N/A",
        "satisfactory": "Satisfactory",
    }
    cleaned_df["current_inspection_rating"] = (
        cleaned_df["current_inspection_rating"]
        .astype("string")
        .str.strip()
        .str.lower()
        .map(rating_mapping)
    )

    text_columns = cleaned_df.select_dtypes(
        include=["object", "string"]
    ).columns
    for column in text_columns:
        cleaned_df[column] = cleaned_df[column].astype(
            "string"
        ).str.strip()

    if cleaned_df["source_url"].isna().any():
        raise ValueError("Some outbreak records are missing URLs.")

    return cleaned_df


def match_outbreaks_to_inspections(inspections, outbreaks):
    """Match outbreak locations to inspection addresses."""
    inspections = inspections.copy()
    outbreaks = outbreaks.copy()

    inspections["address_match"] = (
        inspections["Address"].apply(clean_address)
    )
    outbreaks["location_match"] = (
        outbreaks["location"].apply(clean_address)
    )

    inspection_addresses = (
        inspections[
            ["Address", "City", "Business_ID", "address_match"]
        ]
        .drop_duplicates()
    )

    matches = []
    for _, outbreak in outbreaks.iterrows():
        location = outbreak["location_match"]

        for _, inspection in inspection_addresses.iterrows():
            address = inspection["address_match"]

            if address and address in location:
                matches.append({
                    "food_business": outbreak["food_business"],
                    "location": outbreak["location"],
                    "inspection_address": inspection["Address"],
                    "City": inspection["City"],
                    "Business_ID": inspection["Business_ID"],
                })

    address_matches = pd.DataFrame(
        matches,
        columns=[
            "food_business",
            "location",
            "inspection_address",
            "City",
            "Business_ID",
        ],
    ).drop_duplicates()

    if address_matches.empty:
        raise ValueError(
            "No outbreak locations matched inspection addresses."
        )

    matched_ids = address_matches["Business_ID"].dropna().unique()
    matched_inspections = inspections[
        inspections["Business_ID"].isin(matched_ids)
    ].copy()

    joined_df = matched_inspections.merge(
        address_matches[
            ["food_business", "Business_ID"]
        ].drop_duplicates(),
        on="Business_ID",
        how="left",
    )
    joined_df = joined_df.merge(
        outbreaks.drop(
            columns=["location_match"], errors="ignore"
        ),
        on="food_business",
        how="left",
    )

    return address_matches, joined_df


def create_eda_outputs(joined_df, output_dir):
    """Save missing-data summaries, descriptive statistics, and plots."""
    output_dir.mkdir(parents=True, exist_ok=True)

    missing_data = pd.DataFrame({
        "Missing Count": joined_df.isnull().sum(),
        "Missing Percentage (%)": (
            joined_df.isnull().sum() / len(joined_df) * 100
        ),
    })
    missing_data = missing_data.sort_values(
        by="Missing Percentage (%)", ascending=False
    )
    missing_data.to_csv(
        output_dir / "missing_data_summary.csv"
    )

    quantitative_vars = [
        column for column in [
            "Violation Points",
            "Inspection Score",
            "cases",
            "hospitalizations",
            "deaths",
        ]
        if column in joined_df.columns
    ]
    quantitative_summary = joined_df[
        quantitative_vars
    ].describe().T
    quantitative_summary.to_csv(
        output_dir / "quantitative_summary.csv"
    )

    categorical_vars = [
        column for column in [
            "Violation Type",
            "Inspection Result",
            "Inspection Type",
            "suspected_organism",
            "status",
        ]
        if column in joined_df.columns
    ]

    for column in categorical_vars:
        print(f"\n{column}:")
        print(joined_df[column].value_counts(dropna=False))

    print("\nMissing data summary:")
    print(missing_data)
    print("\nQuantitative summary:")
    print(quantitative_summary)

    if "Violation Type" in joined_df.columns:
        counts = joined_df["Violation Type"].value_counts(
            dropna=False
        )
        plt.figure(figsize=(7, 5))
        sns.barplot(x=counts.index.astype(str), y=counts.values)
        plt.title("Distribution of Food Safety Violation Types")
        plt.xlabel("Violation Type")
        plt.ylabel("Number of Records")
        plt.tight_layout()
        plt.savefig(
            output_dir / "violation_type_distribution.png"
        )
        plt.close()

    if "Inspection Result" in joined_df.columns:
        counts = joined_df["Inspection Result"].value_counts(
            dropna=False
        )
        plt.figure(figsize=(7, 5))
        sns.barplot(x=counts.index.astype(str), y=counts.values)
        plt.title("Distribution of Restaurant Inspection Results")
        plt.xlabel("Inspection Result")
        plt.ylabel("Number of Records")
        plt.xticks(rotation=15)
        plt.tight_layout()
        plt.savefig(
            output_dir / "inspection_result_distribution.png"
        )
        plt.close()

    if "cases" in joined_df.columns:
        outbreak_cases = joined_df.drop_duplicates(
            subset=["source_url"]
        )["cases"].dropna()
        plt.figure(figsize=(7, 5))
        sns.histplot(outbreak_cases, bins=10, kde=False)
        plt.title("Distribution of Reported Foodborne Illness Cases")
        plt.xlabel("Number of Reported Cases")
        plt.ylabel("Number of Outbreak Reports")
        plt.tight_layout()
        plt.savefig(
            output_dir / "outbreak_cases_distribution.png"
        )
        plt.close()


def main():
    """Run outbreak scraping, matching, exports, and EDA."""
    project_dir = Path(__file__).resolve().parent
    output_dir = project_dir / "output"
    inspection_path = project_dir / INSPECTION_FILE

    if not inspection_path.exists():
        raise FileNotFoundError(
            f"Could not find {INSPECTION_FILE}. "
            "Place the inspection CSV in the same folder as this script."
        )

    inspections = pd.read_csv(inspection_path)
    required_columns = {
        "Address",
        "City",
        "Business_ID",
        "Inspection_Serial_Num",
    }
    missing_columns = required_columns.difference(
        inspections.columns
    )
    if missing_columns:
        raise ValueError(
            "The inspection CSV is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    outbreak_df = scrape_outbreak_listing()
    detailed_df = scrape_outbreak_details(outbreak_df)
    outbreaks = clean_outbreak_data(detailed_df)

    output_dir.mkdir(parents=True, exist_ok=True)
    outbreaks.to_csv(
        output_dir / "king_county_foodborne_outbreaks.csv",
        index=False,
        encoding="utf-8-sig",
    )
    print(f"Outbreak records collected: {len(outbreaks)}")

    address_matches, joined_df = match_outbreaks_to_inspections(
        inspections, outbreaks
    )

    print(
        "Restaurants matched:",
        address_matches["food_business"].nunique(),
    )
    print(
        "Unique Business IDs:",
        address_matches["Business_ID"].nunique(),
    )
    print(
        "Unmatched restaurants:",
        outbreaks["food_business"].nunique()
        - address_matches["food_business"].nunique(),
    )
    print("Inspection records:", len(joined_df))
    print(
        "Unique inspections:",
        joined_df["Inspection_Serial_Num"].nunique(),
    )

    address_matches.to_csv(
        output_dir / "outbreak_address_matches.csv",
        index=False,
    )
    joined_df.to_csv(
        output_dir / "outbreak_restaurant_inspections.csv",
        index=False,
    )

    create_eda_outputs(joined_df, output_dir)
    print(f"\nAll output files saved in: {output_dir}")


if __name__ == "__main__":
    main()
