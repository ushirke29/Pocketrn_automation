import streamlit as st
import pandas as pd
import io

# 🔽 Add your image here (local file or URL)
st.image("PocketRN_Logo.png", width=120)  # Adjust width as needed
st.title("PocketRN GUIDE Model Respite Rates By Geography")

st.markdown("Please follow the below instructions for generating updated table of **GUIDE Respite Rates by Zip Code**")
st.markdown("📘 [Instructions Document](https://docs.google.com/document/d/1d1PZjfgPEKe0nJbvP5hJ-HG0Z1w4i19btxGfGJddRTE/edit?tab=t.0#heading=h.guvyizoxu0lz)")

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

**Step 3:** 📦 Extract the ZIP to locate: `Addendum D Geographic Adjustment Factors.xlsx`  

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
***Step 1:** Download:  
**“Actual Regulation Market Basket Updates (ZIP)”**  

**Step 2:** 📦 Extract the ZIP to locate: `Summary Web Table -- Actual (20XXQX)`  

**Step 3:** Upload the file below:
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
# Base Rate Input
# ---------------------------
base_rate = None
if file1 and file2 and file3 and market_adjustment is not None:
    base_rate = st.number_input(
        "💲 Enter Base Hourly Respite Rate ($)",
        min_value=0.0,
        max_value=1000.0,
        value=0.0,
        step=0.25
    )

    if base_rate <= 0:
        st.warning("⚠️ Please enter a base hourly respite rate greater than 0 to proceed.")

# ---------------------------
# Final Report Generation
# ---------------------------
if file1 and file2 and file3 and market_adjustment is not None and base_rate and base_rate > 0:
    if st.button("🚀 Generate Report"):
        try:
            df1 = pd.read_excel(file1) if file1.name.endswith("xlsx") else pd.read_csv(file1, encoding="latin1")
            df2 = pd.read_excel(file2) if file2.name.endswith("xlsx") else pd.read_csv(file2, encoding="latin1")

            df1 = df1[["STATE", "ZIP CODE", "LOCALITY"]]
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
                * base_rate
                * (1 + market_adjustment / 100)
            ).round(2)

            final_df = merged_df[["ZIP CODE", "Locality Name", "Respite Reimbursement Rate ($/hr)"]].copy()
            final_df.rename(columns={"Locality Name": "Geography"}, inplace=True)

            final_df["ZIP CODE"] = final_df["ZIP CODE"].astype(str).str.zfill(5)
            final_df["Geography"] = final_df["Geography"].astype(str).str.replace(r"\*+", "", regex=True).str.strip()
            final_df.replace(to_replace=["nan", "NaT", "None", "NAN"], value="NA", inplace=True)
            final_df.fillna("NA", inplace=True)

            st.subheader("✅ Final Output: ZIP Code, Geography, Respite Reimbursement Rate ($/hr)")
            st.dataframe(final_df)

            # Store in session state to keep download buttons active
            st.session_state["final_df"] = final_df

            st.success("✅ Report generated! Download options appear below.")

        except Exception as e:
            st.error(f"❌ Error during processing: {e}")


# # ---------------------------
# # Base Rate Input + Confirmation
# # ---------------------------
# if file1 and file2 and file3 and market_adjustment is not None:
#     st.markdown("### 💲 Base Hourly Respite Rate Input")
#     base_rate_input = st.number_input(
#         "Enter the Base Hourly Respite Rate ($):",
#         min_value=0.0,
#         max_value=1000.0,
#         value=0.0,
#         step=0.25,
#         key="base_rate_input"
#     )

#     if st.button("✅ Enter Base Rate"):
#         if base_rate_input > 0:
#             st.session_state["confirmed_base_rate"] = base_rate_input
#             st.success(f"Base rate set to ${base_rate_input:.2f}")
#         else:
#             st.warning("⚠️ Please enter a base hourly respite rate greater than 0.")

# # ---------------------------
# # Final Report Generation
# # ---------------------------
# base_rate = st.session_state.get("confirmed_base_rate", None)

# if file1 and file2 and file3 and market_adjustment is not None and base_rate:
#     st.markdown("---")
#     if st.button("🚀 Generate Report"):
#         try:
#             df1 = pd.read_excel(file1) if file1.name.endswith("xlsx") else pd.read_csv(file1, encoding="latin1")
#             df2 = pd.read_excel(file2) if file2.name.endswith("xlsx") else pd.read_csv(file2, encoding="latin1")

#             df1 = df1[["STATE", "ZIP CODE", "LOCALITY"]]
#             df2 = pd.read_excel(
#                 file2,
#                 usecols=["State", "Locality Number", "Locality Name", "2025 GAF (without 1.0 Work Floor)"],
#                 header=2
#             )

#             merged_df = pd.merge(
#                 df1,
#                 df2,
#                 how="left",
#                 left_on=["STATE", "LOCALITY"],
#                 right_on=["State", "Locality Number"]
#             )

#             merged_df["Respite Reimbursement Rate ($/hr)"] = (
#                 merged_df["2025 GAF (without 1.0 Work Floor)"]
#                 * base_rate
#                 * (1 + market_adjustment / 100)
#             ).round(2)

#             final_df = merged_df[["ZIP CODE", "Locality Name", "Respite Reimbursement Rate ($/hr)"]].copy()
#             final_df.rename(columns={"Locality Name": "Geography"}, inplace=True)

#             final_df["ZIP CODE"] = final_df["ZIP CODE"].astype(str).str.zfill(5)
#             final_df["Geography"] = final_df["Geography"].astype(str).str.replace(r"\*+", "", regex=True).str.strip()
#             final_df.replace(to_replace=["nan", "NaT", "None", "NAN"], value="NA", inplace=True)
#             final_df.fillna("NA", inplace=True)

#             st.subheader("✅ Final Output: ZIP Code, Geography, Respite Reimbursement Rate ($/hr)")
#             st.dataframe(final_df)

#             st.session_state["final_df"] = final_df

#             st.success("✅ Report generated! Download options appear below.")

#         except Exception as e:
#             st.error(f"❌ Error during processing: {e}")


# ---------------------------
# Download Buttons (if available)
# ---------------------------
if "final_df" in st.session_state:
    final_df = st.session_state["final_df"]

    # 📤 CSV Export (Excel-safe ZIPs)
    csv_df = final_df.copy()
    csv_df["ZIP CODE"] = csv_df["ZIP CODE"].apply(lambda x: f'="{x}"')
    csv_data = csv_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download CSV (.csv)",
        data=csv_data,
        file_name="Look up Respite Rate.csv",
        mime="text/csv"
    )

    # 📤 Excel Export (text ZIPs)
    xlsx_output = io.BytesIO()
    with pd.ExcelWriter(xlsx_output, engine="xlsxwriter") as writer:
        final_df.to_excel(writer, index=False, sheet_name="Respite Rates")
        workbook = writer.book
        worksheet = writer.sheets["Respite Rates"]
        zip_col_idx = final_df.columns.get_loc("ZIP CODE")
        text_format = workbook.add_format({'num_format': '@'})
        worksheet.set_column(zip_col_idx, zip_col_idx, 12, text_format)

    xlsx_data = xlsx_output.getvalue()
    st.download_button(
        "⬇️ Download Excel (.xlsx)",
        data=xlsx_data,
        file_name="Look up Respite Rate.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
