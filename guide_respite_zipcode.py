import streamlit as st
import pandas as pd
import io

st.image("PocketRN_Logo.png", width=120)
st.title("PocketRN GUIDE Model Respite Rates By Geography")

st.markdown("Please follow the below instructions for generating updated table of **GUIDE Respite Rates by Zip Code**")
st.markdown("📘 [Instructions Document](https://docs.google.com/document/d/1d1PZjfgPEKe0nJbvP5hJ-HG0Z1w4i19btxGfGJddRTE/edit?tab=t.0#heading=h.guvyizoxu0lz)")

# ---------------------------
# File 1 Upload
# ---------------------------
st.markdown("""
**Source:**  
🔗 [CMS Fee Schedules Page](https://www.cms.gov/medicare/payment/fee-schedules)  

**Step 1:** 📁 Download the latest ZIP Code to Carrier Locality file.  
**Step 2:** 📦 Extract and upload the file below:
""")
file1 = st.file_uploader("", type=["xlsx", "csv"], key="file1")

# ---------------------------
# File 2 Upload
# ---------------------------
if file1:
    st.markdown("""
**Source:**  
🔗 [CMS Federal Regulation Notices Page](https://www.cms.gov/medicare/payment/fee-schedules/physician/federal-regulation-notices)  

**Upload the Addendum D Geographic Adjustment Factors file below:**
""")
    file2 = st.file_uploader("", type=["xlsx", "csv"], key="file2")
else:
    file2 = None

# ---------------------------
# Base Rate Input
# ---------------------------
if file1 and file2:
    base_rate = st.number_input("💲 Enter Base Hourly Respite Rate ($)", min_value=0.0, max_value=1000.0, value=0.0, step=0.25)
    if base_rate <= 0:
        st.warning("⚠️ Please enter a base hourly respite rate greater than 0 to proceed.")
else:
    base_rate = None

# ---------------------------
# Final Report Generation
# ---------------------------
if file1 and file2 and base_rate and base_rate > 0:
    if st.button("🚀 Generate Report"):
        try:
            # Load both files
            df1 = pd.read_excel(file1) if file1.name.endswith(".xlsx") else pd.read_csv(file1, encoding="latin1")
            df2 = pd.read_excel(file2, header=2)

            # Select and clean key columns
            df1 = df1[["STATE", "ZIP CODE", "CARRIER", "LOCALITY"]].copy()
            df2 = df2[["Medicare Administrative Contractor (MAC)", "State", "Locality Number", "Locality Name", "2026 GAF (without 1.0 Work Floor)"]].copy()

            # --- Normalize text and numbers ---
            for col in ["STATE", "CARRIER", "LOCALITY"]:
                df1[col] = df1[col].astype(str).str.strip().str.upper()

            for col in ["State", "Medicare Administrative Contractor (MAC)", "Locality Number"]:
                df2[col] = df2[col].astype(str).str.strip().str.upper()

            # zero-pad locality numbers (common CMS issue)
            df1["LOCALITY"] = df1["LOCALITY"].str.zfill(3)
            df2["Locality Number"] = df2["Locality Number"].str.zfill(3)

            # --- Primary merge: STATE + LOCALITY ---
            merged_df = pd.merge(
                df1,
                df2,
                how="left",
                left_on=["STATE", "LOCALITY"],
                right_on=["State", "Locality Number"]
            )

            primary_matches = merged_df["2026 GAF (without 1.0 Work Floor)"].notna().sum()

            # --- Secondary merge: only for missing GAFs ---
            missing_mask = merged_df["2026 GAF (without 1.0 Work Floor)"].isna()
            if missing_mask.any():
                missing_df1 = merged_df.loc[missing_mask, ["STATE", "ZIP CODE", "CARRIER", "LOCALITY"]].copy()
                secondary_merge = pd.merge(
                    missing_df1,
                    df2,
                    how="left",
                    left_on=["CARRIER", "LOCALITY"],
                    right_on=["Medicare Administrative Contractor (MAC)", "Locality Number"]
                )

                secondary_matches = secondary_merge["2026 GAF (without 1.0 Work Floor)"].notna().sum()

                merged_df.loc[missing_mask, "2026 GAF (without 1.0 Work Floor)"] = secondary_merge[
                    "2026 GAF (without 1.0 Work Floor)"
                ].values
                merged_df.loc[missing_mask, "Locality Name"] = secondary_merge["Locality Name"].values
            else:
                secondary_matches = 0

            # --- Compute rates ---
            merged_df["2026 GAF (without 1.0 Work Floor)"] = pd.to_numeric(
                merged_df["2026 GAF (without 1.0 Work Floor)"], errors="coerce"
            )
            merged_df["Respite Reimbursement Rate ($/hr)"] = (
                merged_df["2026 GAF (without 1.0 Work Floor)"] * base_rate
            ).round(2)

            # --- Final table ---
            final_df = merged_df[["ZIP CODE", "Locality Name", "Respite Reimbursement Rate ($/hr)"]].copy()
            final_df.rename(columns={"Locality Name": "Geography"}, inplace=True)
            final_df["ZIP CODE"] = final_df["ZIP CODE"].astype(str).str.zfill(5)
            final_df["Geography"] = final_df["Geography"].fillna("NA").astype(str).str.strip()

            # --- Display summary ---
            st.info(f"✅ Primary matches: {primary_matches:,}")
            st.info(f"🔁 Fallback (MAC+Locality) recovered: {secondary_matches:,}")
            st.info(f"📄 Total ZIPs processed: {len(final_df):,}")

            # --- Show result ---
            st.subheader("✅ Final Output")
            st.dataframe(final_df)

            # Save to session
            st.session_state["final_df"] = final_df

            st.success("✅ Report generated successfully!")

        except Exception as e:
            st.error(f"❌ Error during processing: {e}")


# ---------------------------
# Download Buttons
# ---------------------------
if "final_df" in st.session_state:
    final_df = st.session_state["final_df"]

    csv_df = final_df.copy()
    csv_df["ZIP CODE"] = csv_df["ZIP CODE"].apply(lambda x: f'="{x}"')
    csv_data = csv_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download CSV (.csv)",
        data=csv_data,
        file_name="Look up Respite Rate.csv",
        mime="text/csv"
    )

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
