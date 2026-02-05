import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("Read & Update Google Sheet")

### Google sheet authorization and connection ####

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

client = get_gsheet_client()
sheet = client.open_by_url(st.secrets["config"]["sheet_url"])
worksheet = sheet.worksheet("Sheet1")  


data = worksheet.get_all_records()  

st.subheader("Existing Data")
st.dataframe(data)

st.subheader("Add or Update Record")

name = st.text_input("Name")
email = st.text_input("Email (used as unique key)")
city = st.text_input("City")
score = st.number_input("Score", min_value=0, max_value=100, step=1)

if st.button("Save"):
    try:
        email_list = worksheet.col_values(2)  

        if email in email_list:
            row_index = email_list.index(email) + 1  

            worksheet.update(
                f"A{row_index}:D{row_index}",
                [[name, email, city, score]],
            )

            st.success(f"Updated existing record for {email}")

        else:
            worksheet.append_row([name, email, city, score])
            st.success("New record added")

    except Exception as e:
        st.error("Failed to save data")
        st.error(str(e))
