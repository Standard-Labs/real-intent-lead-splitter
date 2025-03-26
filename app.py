import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import io # Required for handling file uploads in memory

# --- App Configuration ---
st.set_page_config(page_title="Real Intent Leads Splitter", layout="wide")

# --- Helper Functions ---
def process_uploaded_files(uploaded_files):
    """Reads multiple uploaded CSV files and concatenates them into a single DataFrame."""
    if not uploaded_files:
        return pd.DataFrame() # Return empty DataFrame if no files

    all_dfs = []
    error_files = []
    for uploaded_file in uploaded_files:
        try:
            # Use BytesIO to read the uploaded file in memory
            bytes_data = uploaded_file.getvalue()
            s = io.StringIO(bytes_data.decode('utf-8')) # Assuming UTF-8 encoding
            df = pd.read_csv(s)
            if not df.empty:
                all_dfs.append(df)
            else:
                st.warning(f"Uploaded file '{uploaded_file.name}' is empty or could not be read properly.")
        except Exception as e:
            st.error(f"Error reading file '{uploaded_file.name}': {e}")
            error_files.append(uploaded_file.name)

    if not all_dfs:
        st.error("No valid lead data found in the uploaded files.")
        return pd.DataFrame()

    # Concatenate all dataframes
    combined_df = pd.concat(all_dfs, ignore_index=True)
    return combined_df

def generate_csv_download(df, filename):
    """Generates CSV data ready for Streamlit download button."""
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    # Also encode to utf-8 for broad compatibility
    @st.cache_data
    def convert_df(df_to_convert):
       return df_to_convert.to_csv(index=False).encode('utf-8')

    csv_data = convert_df(df)
    return csv_data, filename

# --- Streamlit App UI ---

st.title("🚀 Real Intent Leads Splitter 🚀")
st.markdown("Upload your lead CSV files and assign them randomly to team members.")

st.divider()

# --- Section 1: Enter Names ---
st.header("1. Enter Team Member Names")
st.info("Enter one name per line. Minimum of 2 names required.")

names_input = st.text_area("Team Member Names:", height=150, placeholder="Jonie\nDavid\nSarah\n...")

# Process names: split by newline, strip whitespace, remove empty entries
names = [name.strip() for name in names_input.split('\n') if name.strip()]

if names:
    st.write("Names entered:")
    st.write(names)
    if len(names) < 2:
        st.error("Please enter at least 2 names.")
        names = [] # Reset names if condition not met

st.divider()

# --- Section 2: Upload CSV Files ---
st.header("2. Upload Lead CSV Files")
st.info("Upload up to 10 CSV files containing leads.")

uploaded_files = st.file_uploader(
    "Choose CSV files",
    type="csv",
    accept_multiple_files=True,
    help="Select one or more lead files in CSV format."
)

# Validate number of uploaded files
valid_upload_count = False
if uploaded_files:
    if len(uploaded_files) > 10:
        st.error("You can upload a maximum of 10 files. Please remove some files.")
    else:
        st.success(f"{len(uploaded_files)} file(s) selected.")
        valid_upload_count = True
        # Optionally display filenames
        with st.expander("Show selected filenames"):
            for uploaded_file in uploaded_files:
                st.write(uploaded_file.name)

st.divider()

# --- Section 3: Process and Split Leads ---
st.header("3. Process and Download Split Leads")

# Only proceed if names are valid and files are uploaded correctly
if names and uploaded_files and valid_upload_count:
    st.info("Processing uploaded files...")

    # Read and combine leads
    combined_leads_df = process_uploaded_files(uploaded_files)

    if not combined_leads_df.empty:
        total_leads = len(combined_leads_df)
        num_people = len(names)
        st.success(f"Successfully combined {total_leads} leads from {len(uploaded_files)} file(s).")

        if total_leads < num_people:
            st.warning(f"There are fewer leads ({total_leads}) than people ({num_people}). Some people may not receive any leads.")

        st.write(f"Splitting leads randomly among {num_people} people: {', '.join(names)}")

        # --- Splitting Logic ---
        # 1. Shuffle the combined DataFrame randomly
        shuffled_df = combined_leads_df.sample(frac=1).reset_index(drop=True)

        # 2. Split the shuffled DataFrame into roughly equal parts
        #    np.array_split handles cases where division isn't perfect
        split_dfs = np.array_split(shuffled_df, num_people)

        st.subheader("Download Split Lead Files:")

        # Create download buttons in columns for better layout
        cols = st.columns(min(num_people, 4)) # Create up to 4 columns

        today_str = date.today().strftime("%Y-%m-%d")

        for i, name in enumerate(names):
            if i < len(split_dfs): # Ensure we don't index out of bounds if fewer leads than people
                person_df = split_dfs[i]
                if not person_df.empty:
                    filename = f"leads_{today_str}_{name.replace(' ', '_')}.csv" # Sanitize spaces in names for filename
                    csv_data, download_filename = generate_csv_download(person_df, filename)

                    # Place download button in the next available column
                    col_index = i % len(cols)
                    with cols[col_index]:
                        st.download_button(
                            label=f"Download for {name} ({len(person_df)} leads)",
                            data=csv_data,
                            file_name=download_filename,
                            mime='text/csv',
                            key=f"download_{name}" # Unique key for each button
                        )
                        # Optional: Show a preview
                        # with st.expander(f"Preview for {name}"):
                        #    st.dataframe(person_df.head())
                else:
                    # Handle case where a person gets an empty split (can happen if total_leads < num_people)
                     col_index = i % len(cols)
                     with cols[col_index]:
                        st.write(f"{name}: No leads assigned (due to low total lead count).")

            else:
                 # Handle case where there are more names than splits generated (shouldn't normally happen with np.array_split)
                 col_index = i % len(cols)
                 with cols[col_index]:
                    st.write(f"{name}: No split data available.")


    else:
        st.warning("Could not proceed with splitting as no valid lead data was loaded.")

elif st.button("Process Leads", type="primary"):
    # Show messages if button is clicked but conditions aren't met
    if not names:
        st.error("❌ Please enter at least 2 names in Step 1.")
    if not uploaded_files:
        st.error("❌ Please upload at least one CSV file in Step 2.")
    elif not valid_upload_count:
         st.error("❌ Please ensure you have uploaded 10 or fewer files in Step 2.")

st.divider()
st.caption(f"Real Intent Leads Splitter - © {date.today().year} Real Intent")
