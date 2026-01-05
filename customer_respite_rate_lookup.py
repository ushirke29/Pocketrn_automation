import streamlit as st
import pandas as pd
import os

# Set up page
st.set_page_config(page_title="Respite Lookup", layout="centered")

st.image("PocketRN_Logo.png", width=120)

# Load data for selected year
@st.cache_data
def load_year_data(year):
    filename = f"respite_rate_geography_{year}.csv"
    if not os.path.exists(filename):
        st.error(f"Could not find file: {filename}")
        return None
    
    df = pd.read_csv(filename, dtype={"ZIP CODE": str})
    df["ZIP CODE"] = df["ZIP CODE"].str.extract(r'="?([0-9]+)"?')[0]
    return df

# Custom CSS (unchanged)
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
        width: 100%;
        padding: 30px;
        border-radius: 15px;
        background-color: #f0f4f8;
        box-shadow: 0px 0px 12px rgba(0,0,0,0.05);
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        color: #1f4e79;
        margin-top: 20px;

        display: flex;
        flex-direction: column;

        min-height: 320px;
        justify-content: center;
        align-items: center;
        overflow: hidden;
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

# Title & subtitle (unchanged)
st.markdown('<div class="title"><strong>Respite Reimbursement Rate </strong></div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Search by ZIP Code to view the geography and hourly respite reimbursement rate</div>', unsafe_allow_html=True)

# -----------------------------------------
# ⭐ YEAR + ZIP ON SAME LINE, SAME WIDTH
# -----------------------------------------
year_col, zip_col = st.columns(2)   # equal-width columns

with year_col:
    selected_year = st.selectbox(
        "📅 Select Year:",
        [2025, 2026],
        index=1  # ✅ makes 2026 open by default
    )

# Load data for selected year
df = load_year_data(selected_year)

with zip_col:
    zip_codes = sorted(df["ZIP CODE"].unique()) if df is not None else []
    selected_zip = st.selectbox("📍 Enter ZIP Code:", [""] + zip_codes)

# -----------------------------------------

if not selected_zip:
    st.info("Please select a ZIP Code.")
else:
    row = df[df["ZIP CODE"] == selected_zip]

    if not row.empty:
        geography = row.iloc[0]["Geography"]
        rate = row.iloc[0]["Respite Reimbursement Rate ($/hr)"]

        # ⭐ Dynamic date range based on year
        if selected_year == 2025:
            valid_date_text = "Valid 7/1/2025 – 12/31/2025"
        else:
            valid_date_text = "Valid 1/1/2026 – 12/31/2026"

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f'<div class="card"><div class="label">Geography</div>{geography}</div>',
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f'''
                <div class="card">
                    <div class="label">Respite Rate ($/hr)</div>
                    ${rate:.2f}
                    <div style="font-size: 14px; color: #d9534f; margin-top: 10px;">
                        72 hours annually per client (resets July 1st annually)<br>
                        (Rates and annual respite totals are determined by Medicare and may be adjusted. We will notify partners of any updates.)
                    </div>
                </div>
                ''',
                unsafe_allow_html=True
            )

    else:
        st.warning("ZIP Code not found.")
