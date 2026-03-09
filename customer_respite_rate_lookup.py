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
        return None, None

    df = pd.read_csv(filename, dtype={"ZIP CODE": str})
    df["ZIP CODE"] = df["ZIP CODE"].str.extract(r'="?([0-9]+)"?')[0]

    return df, filename


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

    /* Make multiselect selected tags pink instead of orange */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #c2185b !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600;
    }

    .stMultiSelect [data-baseweb="tag"] span {
        color: white !important;
    }

    /* Download button hover color */
    .stDownloadButton button:hover {
        background-color: #c2185b !important;
        color: white !important;
        border-color: #c2185b !important;
    }

    /* Optional: active click color */
    .stDownloadButton button:active {
        background-color: #a3154d !important;
        color: white !important;
    }

    /* Respite disclaimer text */
    .respite-note {
        font-size: 14px;
        color: #c2185b;
        line-height: 1.4;
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
        index=0
    )

df, filename = load_period_data(selected_period)

with zip_col:
    zip_codes = sorted(df["ZIP CODE"].unique()) if isinstance(df, pd.DataFrame) else []
    selected_zip = st.selectbox("📍 Select your ZIP Code:", [""] + zip_codes)

# -----------------------------------------
# Display results
# -----------------------------------------
if not selected_zip:
    st.info("Please select a ZIP Code.")
else:
    if df is None:
        st.error("Data could not be loaded.")
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

                        <div class="respite-note">
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

# -----------------------------------------
# Download CSV Files
# -----------------------------------------
st.markdown("<br><br>", unsafe_allow_html=True)

st.markdown("### Download Respite Rate Files")
st.write("Select one or more files and download the rate tables.")

download_files = {
    "2025 Rates": "respite_rate_geography_2025.csv",
    "Jan 2026 Rates": "respite_rate_geography_2026_jan.csv",
    "Feb 1, 2026 – Current Rates": "respite_rate_geography_2026_feb.csv"
}

selected_downloads = st.multiselect(
    "Select file(s) to download:",
    list(download_files.keys())
)

for label in selected_downloads:
    file_path = download_files[label]

    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            st.download_button(
                label=f"Download {label}",
                data=f,
                file_name=file_path,
                mime="text/csv"
            )
    else:
        st.warning(f"File not found: {file_path}")
