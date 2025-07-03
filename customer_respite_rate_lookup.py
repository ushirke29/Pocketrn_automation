import streamlit as st
import pandas as pd

# Set up page
st.set_page_config(page_title="Respite Lookup", layout="centered")

st.image("PocketRN_Logo.png", width=120)

# Load and clean data
@st.cache_data
def load_data():
    df = pd.read_csv("respite_rate.csv", dtype={"ZIP CODE": str})
    df["ZIP CODE"] = df["ZIP CODE"].str.extract(r'="?([0-9]+)"?')[0]
    return df

df = load_data()

# Custom CSS styling
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-size: 18px !important;
    }

    .title {
        text-align: center;
        font-size: 44px !important;
        margin-top: 40px;
        color: #333333;
    }

    .subtitle {
        text-align: center;
        font-size: 20px;
        margin-bottom: 50px;
        color: #666;
    }

    .card {
        padding: 30px;
        border-radius: 15px;
        background-color: #f0f4f8;
        box-shadow: 0px 0px 12px rgba(0,0,0,0.05);
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        color: #1f4e79;
        margin-top: 20px;
    }

    .label {
        font-size: 16px;
        color: #555;
        margin-bottom: 10px;
    }

    .stSelectbox > div > div {
        font-size: 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Title & subtitle
st.markdown('<div class="title"><strong>Respite Reimbursement Rate </strong></div>', unsafe_allow_html=True)

st.markdown('<div class="subtitle">Search by ZIP Code to view the geography and hourly respite reimbursement rate</div>', unsafe_allow_html=True)

# ZIP dropdown
zip_codes = sorted(df["ZIP CODE"].unique())
selected_zip = st.selectbox("📍 Select your ZIP Code:", [""] + zip_codes)

# Show placeholder if nothing selected
if not selected_zip:
    st.info("Please type in your zip code to get the GUIDE reimbursement rate.")
else:
    row = df[df["ZIP CODE"] == selected_zip]
    if not row.empty:
        geography = row.iloc[0]["Geography"]
        rate = row.iloc[0]["Respite Reimbursement Rate ($/hr)"]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f'<div class="card"><div class="label">Geography</div>{geography}</div>',
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f'<div class="card"><div class="label">Respite Rate ($/hr)</div>${rate:.2f}</div>',
                unsafe_allow_html=True
            )
    else:
        st.warning("ZIP Code not found.")



