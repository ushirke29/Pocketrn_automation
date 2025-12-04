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
            df2 = pd.read_excel(file2, header=2)

            # Select relevant columns
            df1 = df1[["STATE", "ZIP CODE", "CARRIER", "LOCALITY"]]
            df2 = df2[[
                "Medicare Administrative Contractor (MAC)",
                "State",
                "Locality Number",
                "Locality Name",
                "2025 GAF (without 1.0 Work Floor)"
            ]]

            # ---------------------------
            # Normalize merge keys safely
            # ---------------------------
            df1["STATE"] = df1["STATE"].astype(str).str.strip().str.upper()
            df2["State"] = df2["State"].astype(str).str.strip().str.upper()

            # Safe conversion for LOCALITY and Locality Number
            df1["LOCALITY"] = df1["LOCALITY"].apply(lambda x: str(int(float(x))) if pd.notna(x) else None)
            df2["Locality Number"] = df2["Locality Number"].apply(lambda x: str(int(float(x))) if pd.notna(x) else None)

            # Pad carrier and MAC codes to 5 digits
            df1["CARRIER"] = df1["CARRIER"].astype(str).str.zfill(5)
            df2["Medicare Administrative Contractor (MAC)"] = (
                df2["Medicare Administrative Contractor (MAC)"].astype(str).str.zfill(5)
            )

            # ---------------------------
            # Primary merge: STATE + LOCALITY
            # ---------------------------
            merged_df = pd.merge(
                df1,
                df2,
                how="left",
                left_on=["STATE", "CARRIER", "LOCALITY"],
                right_on=["State", "Medicare Administrative Contractor (MAC)", "Locality Number"]
            )

            primary_matches = merged_df["2025 GAF (without 1.0 Work Floor)"].notna().sum()

            # ---------------------------
            # Fallback merge: MAC + LOCALITY (CARRIER ↔ MAC)
            # ---------------------------
            missing_mask = merged_df["2025 GAF (without 1.0 Work Floor)"].isna()
            if missing_mask.any():
                missing_df1 = df1.loc[missing_mask, ["STATE", "ZIP CODE", "CARRIER", "LOCALITY"]].copy()
                secondary_merge = pd.merge(
                    missing_df1,
                    df2,
                    how="left",
                    left_on=["CARRIER", "LOCALITY"],
                    right_on=["Medicare Administrative Contractor (MAC)", "Locality Number"]
                )

                secondary_matches = secondary_merge["2025 GAF (without 1.0 Work Floor)"].notna().sum()

                # Fill missing from secondary results
                merged_df.loc[missing_mask, "2025 GAF (without 1.0 Work Floor)"] = secondary_merge[
                    "2025 GAF (without 1.0 Work Floor)"
                ].values
                merged_df.loc[missing_mask, "Locality Name"] = secondary_merge["Locality Name"].values
            else:
                secondary_matches = 0

            # ---------------------------
            # Compute Respite Rates
            # ---------------------------
            merged_df["Respite Reimbursement Rate ($/hr)"] = (
                pd.to_numeric(merged_df["2025 GAF (without 1.0 Work Floor)"], errors="coerce") * base_rate
            ).round(2)

            merged_df["Respite Reimbursement Rate ($/hr)"] = merged_df[
                "Respite Reimbursement Rate ($/hr)"
            ].map(lambda x: f"{x:.2f}" if pd.notna(x) else "NA")

            # ---------------------------
            # Prepare Final Output
            # ---------------------------
            final_df = merged_df[["ZIP CODE", "Locality Name", "Respite Reimbursement Rate ($/hr)"]].copy()
            final_df.rename(columns={"Locality Name": "Geography"}, inplace=True)
            final_df["ZIP CODE"] = final_df["ZIP CODE"].astype(str).str.zfill(5)
            final_df["Geography"] = final_df["Geography"].astype(str).str.replace(r"\*+", "", regex=True).str.strip()
            final_df.replace(to_replace=["nan", "NaT", "None", "NAN"], value="NA", inplace=True)
            final_df.fillna("NA", inplace=True)

            # ---------------------------
            # Summary + Output
            # ---------------------------
            st.info(f"✅ Primary matches: {primary_matches:,}")
            st.info(f"🔁 Fallback (MAC+Locality) recovered: {secondary_matches:,}")
            st.info(f"📄 Total ZIPs processed: {len(final_df):,}")

            st.subheader("✅ Final Output: ZIP Code, Geography, Respite Reimbursement Rate ($/hr)")
            st.dataframe(final_df)

            st.session_state["final_df"] = final_df
            st.success("✅ Report generated! Download options appear below.")

        except Exception as e:
            st.error(f"❌ Error during processing: {e}")

# ---------------------------
# Download Buttons
# ---------------------------
if "final_df" in st.session_state:
    final_df = st.session_state["final_df"]

    # CSV export
    csv_df = final_df.copy()
    csv_df["ZIP CODE"] = csv_df["ZIP CODE"].apply(lambda x: f'="{x}"')
    csv_data = csv_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download CSV (.csv)",
        data=csv_data,
        file_name="Look up Respite Rate.csv",
        mime="text/csv"
    )

    # Excel export
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
