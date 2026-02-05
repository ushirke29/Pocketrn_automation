import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import random

st.title("Push Data to Google Sheet")

# -----------------------------------
# Google Sheets client
# -----------------------------------
@st.cache_resource
def get_gsheet_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes,
    )
    return gspread.authorize(creds)

# -----------------------------------
# User inputs (4 columns)
# -----------------------------------
name = st.text_input("Name", value="John Doe")
email = st.text_input("Email", value="john.doe@test.com")
city = st.text_input("City", value="San Francisco")

# dummy random value
score = st.number_input("Score", min_value=0, max_value=100, value=random.randint(50, 90))

# -----------------------------------
# Submit button
# -----------------------------------
if st.button("Submit to Google Sheet"):
    try:
        client = get_gsheet_client()
        sheet = client.open_by_url(st.secrets["config"]["sheet_url"])

        # change sheet name if needed
        worksheet = sheet.worksheet("Sheet1")

        row = [name, email, city, score]

        worksheet.append_row(row)

        st.success("Data successfully added to Google Sheet!")

    except Exception as e:
        st.error("Failed to write to Google Sheet")
        st.error(str(e))
