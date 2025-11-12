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

**Step 2:** 📦 Extract the ZIP to find the file: `ZIP5_APR2026.xlsx`  

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

**Step 2:** Download **“CY 2026 PFS Final Rule Addenda (Updated MM/DD/YYYY)”**  

**Step 3:** 📦 Extract the ZIP to locate: `Addendum D Geographic Adjustment Factors.xlsx`  

**Step 4:** Upload the file below:
""")
    file2 = st.file_uploader("", type=["xlsx", "csv"], key="file2")
else:
    file2 = None

# ---------------------------
# Base Rate Input
# ---------------------------
base_rate = None
if file1 and file2 is not None:
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
if file1 and file2 is not None and base_rate and base_rate > 0:
    if st.button("🚀 Generate Report"):
        try:
            df1 = pd.read_excel(file1) if file1.name.endswith("xlsx") else pd.read_csv(file1, encoding="latin1")
            df2 = pd.read_excel(file2) if file2.name.endswith("xlsx") else pd.read_csv(file2, encoding="latin1")

            df1 = df1[["STATE", "ZIP CODE", "CARRIER", "LOCALITY"]]

            # Normalize 'STATE' codes
            df1["STATE"] = df1["STATE"].replace({
                "EK": "KS",
                "WK": "KS",
                "EM": "MO",
                "WM": "MO"
            })

            df2 = pd.read_excel(
                file2,
                usecols=["Medicare Administrative Contractor (MAC)", "State", "Locality Number", "Locality Name", "2026 GAF (without 1.0 Work Floor)"],
                header=2
            )

            # --- Primary merge: STATE + LOCALITY ---
            merged_df = pd.merge(
                df1,
                df2,
                how="left",
                left_on=["STATE", "LOCALITY"],
                right_on=["State", "Locality Number"]
            )

            # --- Identify rows that didn’t match ---
            missing_mask = merged_df["2026 GAF (without 1.0 Work Floor)"].isna()

            # --- Secondary merge: MAC + LOCALITY (CARRIER ↔ MAC) ---
            if missing_mask.any():
                missing_df1 = df1.loc[missing_mask, ["STATE", "ZIP CODE", "CARRIER", "LOCALITY"]].copy()

                secondary_merge = pd.merge(
                    missing_df1,
                    df2,
                    how="left",
                    left_on=["CARRIER", "LOCALITY"],
                    right_on=["Medicare Administrative Contractor (MAC)", "Locality Number"]
                )

                # Fill missing fields from secondary match
                merged_df.loc[missing_mask, "2026 GAF (without 1.0 Work Floor)"] = secondary_merge[
                    "2026 GAF (without 1.0 Work Floor)"
                ].values
                merged_df.loc[missing_mask, "Locality Name"] = secondary_merge["Locality Name"].values

            # --- Compute Respite Rate ---
            merged_df["Respite Reimbursement Rate ($/hr)"] = (
                merged_df["2026 GAF (without 1.0 Work Floor)"] * base_rate
            ).round(2)

            merged_df["Respite Reimbursement Rate ($/hr)"] = merged_df[
                "Respite Reimbursement Rate ($/hr)"
            ].map("{:.2f}".format)

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
