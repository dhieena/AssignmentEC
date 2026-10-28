import streamlit as st
import pandas as pd
import random
import csv
import os

# Set up page layout
st.set_page_config(
    page_title="TV Program Schedule Optimizer",
    layout="wide"
)

st.title("📺 TV Program Schedule Optimizer")
st.caption("Individual Assignment — Genetic Algorithm Implementation")

# Internal Fixed GA Parameters (Hidden from UI)
GEN = 100
POP = 50
EL_S = 2

# ---------------------------------------------------------
# 1. READ CSV DATA
# ---------------------------------------------------------
def read_csv_to_dict(file_path):
    program_ratings = {}
    with open(file_path, mode='r', newline='') as file:
        reader = csv.reader(file)
        header = next(reader)  # Skip header
        for row in reader:
            if not row:
                continue
            program = row[0]
            ratings = [float(x) for x in row[1:]]
            program_ratings[program] = ratings
    return program_ratings

# Look for modified CSV first; fall back to original if not found
csv_filename = "program_ratings_modified.csv" if os.path.exists("program_ratings_modified.csv") else "program_ratings.csv"

if not os.path.exists(csv_filename):
    st.error(f"CSV file '{csv_filename}' not found. Please ensure 'program_ratings.csv' or 'program_ratings_modified.csv' is uploaded to your repository.")
    st.stop()

# Load dataset dictionary
ratings = read_csv_to_dict(csv_filename)
all_programs = list(ratings.keys())
num_slots = len(next(iter(ratings.values())))
all_time_slots = list(range(6, 6 + num_slots)) 

# ---------------------------------------------------------
# 2. STREAMLIT PARAMETER INPUTS (Main Page Layout)
# ---------------------------------------------------------
st.markdown("---")
st.subheader("⚙️ Genetic Algorithm Parameters")

# Display sliders side-by-side in two columns on the main page
param_col1, param_col2 = st.columns(2)

with param_col1:
    co_r = st.slider(
        "Crossover Rate (CO_R)", 
        min_value=0.00, 
        max_value=0.95, 
        value=0.80, 
        step=0.05,
        help="Range: 0.0 to 0.95 (Default: 0.80)"
    )

with param_col2:
    mut_r = st.slider(
        "Mutation Rate (MUT_R)", 
        min_value=0.01, 
        max_value=0.05, 
        value=0.02, 
        step=0.01,
        help="Range: 0.01 to 0.05 (Default: 0.02)"
