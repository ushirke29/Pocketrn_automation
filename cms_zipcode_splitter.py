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

2. After pasting the ZIP codes, go to  
   **File → Download → Comma-separated values (.csv)**  
   to download your CSV file.

3. Upload that CSV file **here in this tool** using the uploader above.

4. This tool will:
   - Clean and extract all valid ZIP codes 
   - Remove duplicates  
   - Generate one full CSV and multiple chunked CSVs (10,000 rows each)

Once complete, download your files using the buttons provided below.
""")


st.title("📍 Zipcode Splitter (Excel-Safe ZIP Codes)")

MAX_ROWS = 10000

uploaded_file = st.file_uploader(
    "Upload CSV containing a 'zip_codes' column",
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

        if "zip_codes" not in df.columns:
            st.error("❌ CSV must contain a column named 'zip_codes'.")
            st.stop()

        collected = []
        total_input_rows = len(df)

        for _, row in df.iterrows():
            raw = str(row["zip_codes"])
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
            {"zip_codes": [f'="{z}"' for z in unique_zipcodes]},
            dtype=str
        )

        # Chunk stats
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
        **Chunk size:** {MAX_ROWS} rows  
        **Total output chunk files:** {num_files}  
        """)

        # ------------------------
        # Display output table
        # ------------------------
        st.subheader("📌 Final ZIP Codes (Excel-friendly, leading zeros preserved)")
        st.write(f"Total ZIP entries: **{final_unique_count}**")
        st.dataframe(df_excel)

        # ------------------------
        # EXPORT FUNCTIONS
        # ------------------------

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

                # Strict sequential slicing → guarantees no duplicates
                chunk = df_output.iloc[start:end]

                buf = StringIO()
                chunk.to_csv(buf, index=False, quoting=csv.QUOTE_MINIMAL)

                st.download_button(
                    f"📥 Download cms_zipcodes_{i+1}.csv ({len(chunk)} rows)",
                    buf.getvalue(),
                    f"cms_zipcodes_{i+1}.csv",
                    mime="text/csv"
                )

        # ------------------------
        # DOWNLOADS
        # ------------------------
        st.markdown("## ⬇️ Downloads")

        export_single_file(df_excel)
        export_chunks(df_excel)

        st.success("🎉 Done! All chunk files contain distinct ZIP codes with correct filenames.")

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
