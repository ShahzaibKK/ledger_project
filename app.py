import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from io import StringIO
from pathlib import Path

# Define your credentials
username = "shahzaibkk"
password = "PAKistan1122"

store_data = Path(".\.data")
print(store_data)


def save_ledger_to_excel(ledger_html_file):
    # Read the saved HTML file
    with open(ledger_html_file, "r", encoding="utf-8") as file:
        ledger_html = file.read()

    # Parse the HTML using BeautifulSoup
    ledger_soup = BeautifulSoup(ledger_html, "html.parser")

    # Find all tables in the HTML
    tables = ledger_soup.find_all("table", class_="tablee")

    if not tables:
        print("No tables found in the HTML.")
        return

    # Initialize an empty list to store DataFrames for each table
    dfs = []

    # Convert each HTML table to a DataFrame and store in the list
    for table in tables:
        df = pd.read_html(StringIO(str(table)), parse_dates=True)[0]
        dfs.append(df)

    # Concatenate all DataFrames into a single DataFrame
    combined_df = pd.concat(dfs, ignore_index=False)

    # Extract Grade and Size from the "remark" column
    combined_df["Grade"] = combined_df["Remarks"].str.extract(
        r"\b(Premium|Standard|Commercial)\b"
    )
    combined_df["Size"] = combined_df["Remarks"].str.extract(r"(\d+x\d+)")
    combined_df["BH"] = combined_df["Remarks"].str.extract(r"(\bBH\b)")

    # Create a dictionary to map sizes to corresponding packing values
    packings = {"10x20": 1.5, "12x24": 1.44, "12x12": 1.1, "16x16": 1.6}

    # Check the "Size" column and create the "Packing" column with corresponding packing values
    combined_df["Packing"] = combined_df["Size"].map(packings, na_action="ignore")

    # Save the combined DataFrame to an Excel file
    combined_df.to_excel(store_data / "account_ledger.xlsx", index=False)
    print("Table data saved to account_ledger.xlsx")


# Create a session
session = requests.Session()

# Retrieve the login page
login_url = "https://ktp.tiletraders.pk/"  # Update with the actual login URL
login_page = session.get(login_url)

# Check if retrieval was successful
if login_page.status_code == 200:
    # Extract the login form data
    login_soup = BeautifulSoup(login_page.content, "html.parser")
    form = login_soup.find("form")
    login_data = {}
    for input_tag in form.find_all("input"):
        if input_tag.get("name"):
            login_data[input_tag["name"]] = input_tag.get("value", "")

    # Add your credentials to the form data
    login_data["username"] = username
    login_data["password"] = password

    # Submit the login form
    login_response = session.post(login_url, data=login_data)

    # Check if login was successful
    if login_response.status_code == 200:
        print("Login successful!")
        # Now you can access the protected resource
        url_ledger = "https://ktp.tiletraders.pk/Reports/account_ledger"  # Update with the actual URL

        # Define parameters for the ledger request
        start_date = datetime(2024, 1, 1)
        final_date = datetime(2024, 2, 29)

        ledger_params = {
            "start": start_date.strftime("%d-%m-%Y"),  # Format date as DD-MM-YYYY
            "final": final_date.strftime("%d-%m-%Y"),  # Format date as DD-MM-YYYY
            "ac_id": "258",  # Update with the account ID you want to retrieve
            "ledger_show_type": "item_wise",  # Update with the ledger type you want to retrieve
            "search_date": "yes",
            "tt_id": "8",  # Voucher Type
        }
        # Send a POST request to retrieve the ledger for the selected account
        ledger_response = session.post(url_ledger, data=ledger_params)
        # Check if ledger retrieval was successful
        if ledger_response.status_code == 200:
            print("Ledger retrieved successfully!")
            # Save the HTML response to a file
            ledger_html_file = store_data / "account_ledger.html"
            with open(ledger_html_file, "w", encoding="utf-8") as file:
                file.write(ledger_response.text)

            # Call the function to save the table data to an Excel file
            save_ledger_to_excel(ledger_html_file)
        else:
            print("Failed to retrieve ledger:", ledger_response.status_code)
    else:
        print("Login failed:", login_response.status_code)
else:
    print("Failed to retrieve login page:", login_page.status_code)
