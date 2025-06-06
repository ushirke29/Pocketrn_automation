


import streamlit as st
import pandas as pd

st.title("📊 GUIDE Respite Rates by Zip Code Generator")

st.markdown("Please follow the below instructions for generating updated table of **GUIDE Respite Rates by Zip Code**")
st.markdown("For more detail explanation please look into this instructions document: [How to Generate Updated Table of GUIDE Respite Rates by Zip Code](https://docs.google.com/document/d/1d1PZjfgPEKe0nJbvP5hJ-HG0Z1w4i19btxGfGJddRTE/edit?tab=t.0#heading=h.guvyizoxu0lz)")
# ---------------------------
# File 1: ZIP Code to Carrier Locality
# ---------------------------
st.markdown("""
**Source:**  
🔗 [CMS Fee Schedules Page](https://www.cms.gov/medicare/payment/fee-schedules)  

**Step 1:** 📁 Download the latest ZIP Code to Carrier Locality file titled:  
**“Zip Code to Carrier Locality File - Revised MM/DD/YYYY”**  

**Step 2:** 📦 Extract the ZIP to find the file: `ZIP5_APR2025.xlsx`  

**Step 3:** Upload the Excel or CSV file below:
""")
file1 = st.file_uploader("", type=["xlsx", "csv"], key="file1")

# ---------------------------
# File 2: Addendum D GAF
# ---------------------------
if file1:
    st.markdown("""
**Source:**  
🔗 [CMS Federal Regulation Notices Page](https://www.cms.gov/medicare/payment/fee-schedules/physician/federal-regulation-notices)  

**Step 1:** Find the most recent file titled:  
**“CMS-1807-F”**  

**Step 2:** Download **“CY 2025 PFS Final Rule Addenda (Updated MM/DD/YYYY)”**  

**Step 3:** 📦 Extract the ZIP to locate:  
`Addendum D Geographic Adjustment Factors.xlsx`  

**Step 4:** Upload the file below:
""")
    file2 = st.file_uploader("", type=["xlsx", "csv"], key="file2")
else:
    file2 = None

# ---------------------------
# File 3: Market Basket PPS Summary
# ---------------------------
if file2:
    st.markdown("""
**Source:**  
🔗 [CMS Market Basket Data Page](https://www.cms.gov/research-statistics-data-and-systems/statistics-trends-and-reports/medicareprogramratesstats/marketbasketdata)  

**Step 1:** Download the ZIP titled:  
**“Actual Regulation Market Basket Updates (ZIP)”**  

**Step 2:** 📦 Extract the ZIP to locate:  
`Summary Web Table – Actual.xlsx`  

**Step 3:** Upload the Excel file below:
""")
    file3 = st.file_uploader("", type=["xlsx", "csv"], key="file3")
else:
    file3 = None

# ---------------------------
# Market Basket Adjustment Extraction
# ---------------------------
market_adjustment = None
selected_year_col = None

if file3:
    try:
        pps_df = pd.read_excel(file3, header=None)
        hha_row_index = pps_df[pps_df[0].astype(str).str.contains("Home Health Agency PPS", case=False, na=False)].index[0]
        headers = pps_df.iloc[hha_row_index]
        valid_columns = headers.notna()
        data_block = pps_df.iloc[hha_row_index + 1:hha_row_index + 4].copy()
        data_block = data_block.loc[:, valid_columns]
        clean_headers = headers[valid_columns].tolist()

        def make_unique_columns(cols):
            seen = {}
            unique = []
            for col in cols:
                if col not in seen:
                    seen[col] = 0
                    unique.append(col)
                else:
                    seen[col] += 1
                    unique.append(f"{col}_{seen[col]}")
            return unique

        data_block.columns = make_unique_columns(clean_headers)
        fy_cols = sorted([col for col in data_block.columns if isinstance(col, str) and col.startswith("FY")])
        cy_cols = sorted([col for col in data_block.columns if isinstance(col, str) and col.startswith("CY")])
        year_columns = fy_cols + cy_cols

        selected_year_col = st.selectbox("📅 Select Year Column for Market Adjustment", year_columns)

        mb_row = data_block[data_block.iloc[:, 0].astype(str).str.contains("Market Basket Update less Productivity Adjustment", case=False, na=False)]
        market_adjustment = float(mb_row[selected_year_col].values[0])

        st.success(f"✅ Market Adjustment for {selected_year_col}: {market_adjustment}%")
    except Exception as e:
        st.warning(f"⚠️ Could not extract Market Basket Adjustment: {e}")

# ---------------------------
# Final Report Generation
# ---------------------------
if file1 and file2 and file3 and market_adjustment is not None:
    if st.button("🚀 Generate Report"):
        try:
            # ✅ UPDATED: Read both CSV/XLSX formats correctly
            df1 = pd.read_excel(file1) if file1.name.endswith("xlsx") else pd.read_csv(file1, encoding="latin1")
            df2 = pd.read_excel(file2) if file2.name.endswith("xlsx") else pd.read_csv(file2, encoding="latin1")

            df1 = df1[["STATE", "ZIP CODE", "LOCALITY"]]
            # Clean column names
            df2 = pd.read_excel(
                file2,
                usecols=["State", "Locality Number", "Locality Name", "2025 GAF (without 1.0 Work Floor)"],
                header=2
            )


            merged_df = pd.merge(
                df1,
                df2,
                how="left",
                left_on=["STATE", "LOCALITY"],
                right_on=["State", "Locality Number"]
            )

            merged_df["Respite Reimbursement Rate ($/hr)"] = (
                merged_df["2025 GAF (without 1.0 Work Floor)"]
                * 33.75
                * (1 + market_adjustment / 100)
            ).round(2)

            final_df = merged_df[["ZIP CODE", "Locality Name", "Respite Reimbursement Rate ($/hr)"]].copy()
            final_df.rename(columns={"Locality Name": "Geography"}, inplace=True)
            final_df["Geography"] = final_df["Geography"].astype(str).str.replace(r"\*+", "", regex=True).str.strip()

            # Clean Geography and replace NaNs
            final_df["Geography"] = final_df["Geography"].astype(str).str.replace(r"\*+", "", regex=True).str.strip()
            final_df.replace(to_replace=["nan", "NaT", "None", "NAN"], value="NA", inplace=True)
            final_df.fillna("NA", inplace=True)

            st.subheader("✅ Final Output: ZIP Code, Geography, Respite Reimbursement Rate ($/hr)")
            st.dataframe(final_df)

            csv_data = final_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download Final CSV",
                data=csv_data,
                file_name="Look up Respite Rate.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"❌ Error during processing: {e}")
else:
    st.info("📥 Please upload all three files and select a year column to enable report generation.")
