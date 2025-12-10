import streamlit as st
import pandas as pd
import re
from io import StringIO
import csv
import math


st.markdown("""
### 📝 Instructions

1. **Open the Google Sheet and paste your ZIP codes** into the column provided:  
   👉 [Google Sheet Link](https://docs.google.com/spreadsheets/d/1sSK1vinAysZmh7nyf2ZtMi1kZSKvdVkna_qgYIKqDBg/edit?gid=0#gid=0)

2. After pasting the ZIP codes, please change the column name to the exact column name as mentioned in the CMS template and then go to  
   **File → Download → Comma-separated values (.csv)**  
   to download your CSV file.

3. Upload that CSV file **here in this tool** using the uploader above.

4. This tool will:
   - Clean and extract all valid ZIP codes 
   - Remove duplicates  
   - Generate one full CSV and multiple chunked CSVs (Excel-safe ≤ 10,000 rows each)
""")


st.title("📍 Zipcode Splitter (Excel-Safe ZIP Codes)")

# Excel max rows = 10,000 → so ZIP rows = 9,999 (header = 1 row)
MAX_ROWS = 9999

uploaded_file = st.file_uploader(
    "Upload CSV containing a 'Zip_Codes' column",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        df = pd.read_csv(
            uploaded_file,
            dtype=str,
            keep_default_na=False,
            na_filter=False
        )

        if "Zip_Codes" not in df.columns:
            st.error("❌ CSV must contain a column named 'Zip_Codes'.")
            st.stop()

        collected = []
        total_input_rows = len(df)

        for _, row in df.iterrows():
            raw = str(row["Zip_Codes"])
            if raw.strip() == "":
                continue

            parts = re.split(r"[,\s;\|/\\\-]+", raw)

            for z in parts:
                z = z.strip()
                if z == "":
                    continue
                if re.search(r"[A-Za-z]", z):
                    continue
                if not z.isdigit():
                    continue
                if z == "000":
                    continue

                collected.append(z)

        # Stats BEFORE deduplication
        total_parsed_zipcodes = len(collected)

        # GLOBAL DEDUPLICATION
        unique_zipcodes = list(dict.fromkeys(collected))
        final_unique_count = len(unique_zipcodes)

        # Excel-safe formatting
        df_excel = pd.DataFrame(
            {"Zip_Codes": [f'="{z}"' for z in unique_zipcodes]},
            dtype=str
        )

        # Correct chunk calculation for 9,999 rows + header
        num_files = max(1, math.ceil(final_unique_count / MAX_ROWS))

        # ------------------------
        # 📊 SUMMARY PANEL
        # ------------------------
        st.markdown("## 📊 Processing Summary")

        st.markdown(f"""
        **Total input rows:** {total_input_rows}  
        **Total ZIP entries parsed:** {total_parsed_zipcodes}  
        **Duplicate ZIPs removed:** {total_parsed_zipcodes - final_unique_count}  
        **Final unique ZIP count:** {final_unique_count}  
        **Chunk size:** {MAX_ROWS} ZIP rows per file  
        **Total output chunk files:** {num_files}  
        """)

        # Display output table
        st.subheader("📌 Final ZIP Codes (Excel-friendly, leading zeros preserved)")
        st.write(f"Total ZIP entries: **{final_unique_count}**")
        st.dataframe(df_excel)

        st.markdown("""
        ### ⚠️ Important Notice  
        **Please open the downloaded CSV files in Microsoft Excel — NOT in Apple Numbers.**  
        Numbers may not let you upload the data in the same format required for the CMS file upload.

        If the CMS portal does not accept the file or gives an error while uploading, please follow these steps:

        1. Open the downloaded file in **Excel**.  
        2. Copy the **header name** from CMS provided template into a new Excel workbook.  
        3. Save the new workbook as a **CSV (Comma delimited) (.csv)** file.  
        4. Upload this new CSV file to the CMS portal.

        This ensures the correct encoding and formatting required by CMS.
        """)


        # EXPORT FUNCTIONS
        def export_single_file(df_output):
            buf = StringIO()
            df_output.to_csv(buf, index=False, quoting=csv.QUOTE_MINIMAL)

            st.download_button(
                "📥 Download FULL file",
                buf.getvalue(),
                "cms_zipcodes_full.csv",
                mime="text/csv"
            )

        def export_chunks(df_output):
            for i in range(num_files):
                start = i * MAX_ROWS
                end = start + MAX_ROWS

                chunk = df_output.iloc[start:end]

                buf = StringIO()
                chunk.to_csv(buf, index=False, quoting=csv.QUOTE_MINIMAL)

                st.download_button(
                    f"📥 Download cms_zipcodes_{i+1}.csv ({len(chunk)} rows)",
                    buf.getvalue(),
                    f"cms_zipcodes_{i+1}.csv",
                    mime="text/csv"
                )

        # DOWNLOAD BUTTONS
        st.markdown("## ⬇️ Downloads")

        export_single_file(df_excel)
        export_chunks(df_excel)

        st.success("🎉 Done! Chunk files are now capped at 9,999 ZIP rows (10,000 including header).")

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
