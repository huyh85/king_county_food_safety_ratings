import requests
import pandas as pd
import re
import string
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup

BASE_URL = "https://kingcounty.gov/en/dept/dph/health-safety/disease-illness/foodborne-illness-outbreaks"

headers = {
    "User-Agent": "Mozilla/5.0"
}

detail_headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE_URL
}

from urllib.parse import urljoin

# Download and parse the main outbreak webpage
response = requests.get(BASE_URL, headers=headers, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")
tables = soup.find_all("table")

outbreak_records = []

# Extract local King County outbreaks from the first three tables
for table in tables[:3]:
    for row in table.find_all("tr"):
        cells = row.find_all("td")

        # Skip header rows and rows without all four expected columns
        if len(cells) < 4:
            continue

        # Only keep rows containing a valid outbreak detail-page link
        link = cells[2].find("a", href=True)
        if link is None:
            continue

        outbreak_records.append({
            "date_posted": cells[0].get_text(" ", strip=True),
            "last_updated": cells[1].get_text(" ", strip=True),
            "food_business": cells[2].get_text(" ", strip=True),
            "suspected_organism": cells[3].get_text(" ", strip=True),
            "source_url": urljoin(BASE_URL, link["href"])
        })

outbreak_df = pd.DataFrame(outbreak_records)

# Visit each outbreak page and extract its additional information
all_details = []

for _, row in outbreak_df.iterrows():
    url = row["source_url"]

    try:
        page_response = requests.get(
            url, headers=detail_headers, timeout=30
        )
        page_response.raise_for_status()

        page_soup = BeautifulSoup(page_response.text, "html.parser")
        table = page_soup.find("table")

        details = {}

        if table:
            cells = table.find_all(["th", "td"])

            for i in range(1, len(cells) - 1, 2):
                label = cells[i].get_text(" ", strip=True)
                value = cells[i + 1].get_text(" ", strip=True)
                details[label] = value

        record = row.to_dict()
        record.update(details)
        all_details.append(record)

    except requests.RequestException as e:
        print(f"Failed to scrape {url}: {e}")

detailed_df = pd.DataFrame(all_details)

# Confirm every outbreak record has a detail-page URL
if outbreak_df["source_url"].isna().any():
    raise ValueError("Some outbreak records are missing URLs.")

# Standardize variations in column labels across outbreak pages
column_groups = {
    "cases": ["Cases"],
    "hospitalizations": ["Hospitalizations"],
    "deaths": ["Deaths"],
    "status": ["Status"],
    "location": ["Location"],
    "meal_date_range": [
        "Meal Date Range", "Meal Date", "Meal date",
        "Meal dates", "Meal date range"
    ],
    "illness_onset_date_range": [
        "Illness Onset Date Range", "Illness Onset Date",
        "Illness onset date range", "Illness onset date range:"
    ],
    "current_inspection_rating": [
        "Current Inspection Rating", "Current inspection rating"
    ],
    "date_suspected_products_were_purchased": [
        "Date suspected products were purchased:"
    ]
}

# Keep the main outbreak information
base_columns = [
    "date_posted", "last_updated", "food_business",
    "suspected_organism", "source_url"
]

cleaned_df = detailed_df[base_columns].copy()

# Combine differently named fields into standardized columns
for new_column, old_columns in column_groups.items():
    available_columns = [
        col for col in old_columns if col in detailed_df.columns
    ]

    cleaned_df[new_column] = (
        detailed_df[available_columns]
        .bfill(axis=1)
        .iloc[:, 0]
        if available_columns else None
    )

# Convert numerical fields and dates to appropriate data types
for column in ["cases", "hospitalizations", "deaths"]:
    cleaned_df[column] = pd.to_numeric(
        cleaned_df[column], errors="coerce"
    )

# Convert dates with different formats into datetime objects
for column in ["date_posted", "last_updated"]:
    cleaned_df[column] = pd.to_datetime(
        cleaned_df[column],
        format="mixed",
        errors="coerce"
    )
# Standardize investigation status
status_mapping = {
    "investigation is complete": "Completed",
    "investigation is completed": "Completed",
    "investigation in completed": "Completed",
    "investigation is ongoing": "Ongoing"
}

cleaned_df["status"] = (
    cleaned_df["status"].str.strip().str.lower().map(status_mapping)
)

# Standardize inspection ratings
rating_mapping = {
    "good": "Good",
    "okay": "Okay",
    "needs to improve": "Needs to Improve",
    "excellent": "Excellent",
    "n/a": "N/A",
    "satisfactory": "Satisfactory"
}

cleaned_df["current_inspection_rating"] = (
    cleaned_df["current_inspection_rating"]
    .str.strip().str.lower().map(rating_mapping)
)

# Remove extra whitespace from text fields
text_columns = cleaned_df.select_dtypes(include=["object", "str"]).columns

for column in text_columns:
    cleaned_df[column] = cleaned_df[column].str.strip()

# Export the cleaned database
cleaned_df.to_csv(
    "king_county_foodborne_outbreaks.csv",
    index=False,
    encoding="utf-8-sig"
)

print(f"Database exported: {len(cleaned_df)} records")


# Standardize addresses
def clean_address(address):
    if pd.isna(address):
        return ""

    address = str(address).upper()
    address = address.translate(
        str.maketrans("", "", string.punctuation)
    )
    return " ".join(address.split())


# Standardize inspection addresses
inspections["address_match"] = (
    inspections["Address"].apply(clean_address)
)

# Standardize the full outbreak location
outbreaks["location_match"] = (
    outbreaks["location"].apply(clean_address)
)

# Get unique inspection addresses
inspection_addresses = (
    inspections[["Address", "City", "Business_ID", "address_match"]]
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
                "Business_ID": inspection["Business_ID"]
            })


# Create matching dataframe
address_matches = pd.DataFrame(matches).drop_duplicates()

print(
    "Restaurants matched:",
    address_matches["food_business"].nunique()
)

print(
    "Unique Business IDs:",
    address_matches["Business_ID"].nunique()
)

display(address_matches)

matched_restaurants = address_matches["food_business"].unique()

unmatched_restaurants = outbreaks[
    ~outbreaks["food_business"].isin(matched_restaurants)
][["food_business", "location"]]

print("Unmatched restaurants:", len(unmatched_restaurants))

display(unmatched_restaurants)

# Match all inspection records using the identified Business IDs
matched_ids = address_matches["Business_ID"].unique()

matched_inspections = inspections[
    inspections["Business_ID"].isin(matched_ids)
].copy()

# Attach outbreak information
joined_df = matched_inspections.merge(
    address_matches[
        ["food_business", "Business_ID"]
    ].drop_duplicates(),
    on="Business_ID",
    how="left"
)

joined_df = joined_df.merge(
    outbreaks.drop(columns=["location_match"], errors="ignore"),
    on="food_business",
    how="left"
)

# Check results
print("Matched restaurants:", joined_df["food_business"].nunique())
print("Inspection records:", len(joined_df))
print("Unique inspections:",
      joined_df["Inspection_Serial_Num"].nunique())

joined_df.to_csv(
    "outbreak_restaurant_inspections.csv",
    index=False
)

print("Database exported!")

missing_data = pd.DataFrame({
    "Missing Count": joined_df.isnull().sum(),
    "Missing Percentage (%)": (
        joined_df.isnull().sum() / len(joined_df) * 100
    )
})

display(
    missing_data.sort_values(
        by="Missing Percentage (%)",
        ascending=False
    )
)

# Quantitative variables
quantitative_vars = [
    "Violation Points",
    "Inspection Score",
    "cases",
    "hospitalizations",
    "deaths"
]

display(joined_df[quantitative_vars].describe().T)

# Categorical variables
categorical_vars = [
    "Violation Type",
    "Inspection Result",
    "Inspection Type",
    "suspected_organism",
    "status"
]

for col in categorical_vars:
    print(f"\n{col}:")
    print(joined_df[col].value_counts(dropna=False))

quantitative_vars = [
    "Violation Points",
    "Inspection Score",
    "cases",
    "hospitalizations",
    "deaths"
]

quantitative_summary = joined_df[quantitative_vars].describe().T
display(quantitative_summary)

violation_counts = joined_df["Violation Type"].value_counts()

plt.figure(figsize=(7, 5))
sns.barplot(
    x=violation_counts.index,
    y=violation_counts.values
)

plt.title("Distribution of Food Safety Violation Types")
plt.xlabel("Violation Type")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.show()

result_counts = joined_df["Inspection Result"].value_counts()

plt.figure(figsize=(7, 5))
sns.barplot(
    x=result_counts.index,
    y=result_counts.values
)

plt.title("Distribution of Restaurant Inspection Results")
plt.xlabel("Inspection Result")
plt.ylabel("Number of Records")
plt.xticks(rotation=15)
plt.tight_layout()
plt.show()

plt.figure(figsize=(7, 5))

sns.histplot(
    joined_df["cases"].drop_duplicates(),
    bins=10,
    kde=False
)

plt.title("Distribution of Reported Foodborne Illness Cases")
plt.xlabel("Number of Reported Cases")
plt.ylabel("Frequency")
plt.tight_layout()
plt.show()
