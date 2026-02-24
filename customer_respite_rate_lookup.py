import streamlit as st
import pandas as pd
import os
import streamlit.components.v1 as components


# -----------------------------------------
# Page configuration
# -----------------------------------------
st.set_page_config(page_title="Respite Lookup", layout="centered")
st.image("PocketRN_Logo.png", width=120)

# -----------------------------------------
# Data loader
# -----------------------------------------
@st.cache_data
def load_period_data(period_key):
    filename_map = {
        "2025": "respite_rate_geography_2025.csv",
        "Jan 2026": "respite_rate_geography_2026_jan.csv",
        "Feb 1, 2026 – Current": "respite_rate_geography_2026_feb.csv",
    }

    filename = filename_map.get(period_key)

    if not filename or not os.path.exists(filename):
        st.error(f"Could not find file: {filename}")
        return None

    df = pd.read_csv(filename, dtype={"ZIP CODE": str})
    df["ZIP CODE"] = df["ZIP CODE"].str.extract(r'="?([0-9]+)"?')[0]
    return df

# -----------------------------------------
# Custom CSS
# -----------------------------------------
st.markdown("""
    <style>
    html, body, [class*="css"] {
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
        line-height: 1.35;

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
        justify-content: flex-start;
        align-items: center;
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

# -----------------------------------------
# Title
# -----------------------------------------
st.markdown(
    '<div class="title"><strong>Respite Reimbursement Rate</strong></div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">Search by ZIP Code to view the geography and hourly respite reimbursement rate</div>',
    unsafe_allow_html=True
)

# -----------------------------------------
# Period + ZIP selectors
# -----------------------------------------

period_col, zip_col = st.columns(2)

with period_col:
    selected_period = st.selectbox(
        "📅 Select Period:",
        ["2025", "Jan 2026", "Feb 1, 2026 – Current"],
        index=2
    )

df = load_period_data(selected_period)

with zip_col:
    zip_codes = sorted(df["ZIP CODE"].unique()) if df is not None else []
    selected_zip = st.selectbox("📍 Select your ZIP Code:", [""] + zip_codes)


# -----------------------------------------
# Display results
# -----------------------------------------
if not selected_zip:
    st.info("Please select a ZIP Code.")
else:
    row = df[df["ZIP CODE"] == selected_zip]

    if not row.empty:
        geography = row.iloc[0]["Geography"]
        rate = float(row.iloc[0]["Respite Reimbursement Rate ($/hr)"])

        if selected_period == "2025":
            valid_date_text = "Valid 7/1/2025 – 12/31/2025"
        elif selected_period == "Jan 2026":
            valid_date_text = "Valid 1/1/2026 – 1/31/2026"
        elif selected_period == "Feb 1, 2026 – Current":
            valid_date_text = "Valid from 2/1/2026 and onwards"
        else:
            valid_date_text = None


        col1, col2 = st.columns(2)

        # Geography card
        with col1:
            st.markdown(
                f"""
        <div class="card">
            <div class="label" style="margin-bottom: 14px;">Geography</div>
            <div style="font-size: 26px; font-weight: 700;">
                {geography}
            </div>
        </div>
        """,
                unsafe_allow_html=True
            )

        
        with col2:
            st.markdown(
                f"""
        <div class="card">
        <div class="label">Respite Rate ($/hr)</div>

        <div style="font-size: 32px; font-weight: 800; margin: 6px 0;">
            ${rate:.2f}
        </div>

        <div style="font-size: 15px; font-weight: 700; color: #444; margin-bottom: 10px;">
            {valid_date_text}
        </div>

        <div style="font-size: 14px; color: #d9534f; line-height: 1.4;">
            72 hours annually per client (resets July 1st annually)<br>
            (Rates and annual respite totals are determined by Medicare and may be adjusted.
            We will notify partners of any updates.)
        </div>
        </div>
        """,
                unsafe_allow_html=True
            )


    else:
        st.warning("ZIP Code not found.")

