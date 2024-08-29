import streamlit as st
import pandas as pd
import numpy as np
import io

# Custom CSS to improve the look and feel
st.markdown("""
<style>
    .main {
        background-color: #1E1E1E;
        color: white;
    }
    .stButton>button {
        color: white;
        background-color: #4CAF50;
        border: none;
        border-radius: 4px;
        padding: 10px 24px;
    }
    .stTextInput>div>div>input {
        color: white;
        background-color: #333333;
    }
    .stSlider>div>div>div>div {
        background-color: #4CAF50;
    }
    .stHeader {
        background-color: #4CAF50;
        padding: 20px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div style='display: flex; justify-content: space-between; align-items: center; background-color: #333333; padding: 10px; border-radius: 5px;'>
    <h1 style='color: white;'>TEST PORTAL</h1>
    <div>
        <button style='background-color: #FFA500; color: black; border: none; padding: 5px 10px; border-radius: 3px;'>HOME</button>
        <span style='color: white; margin-left: 10px;'>Welcome Michael Hawkins</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Instructions
st.markdown("""
###Instructions
1. **Upload CSV File**: 
   - The CSV should have the following columns:
     - Entity: Data element for which you want to find a match
     - Type: "Test" for test entity, "Not Test" for control entities
     - Date: In mm/dd/yyyy format
     - Filter: Category for filtering data
     - Metric columns: Any number of metric columns (e.g., Sales $, Sales Qty, etc.)

2. **Enter Weights**: 
   - Assign weights (0-10) to each metric to determine their importance in matching

3. **Specify Number of Control Stores**: 
   - Enter the number of control stores you want to find for each test store

4. **Generate Results**: 
   - Click "Generate Control Stores" to find the best matches based on your inputs
""")


def validate_csv(df):
    required_columns = ['Entity', 'Type', 'Date', 'Filter']
    if not all(col in df.columns for col in required_columns):
        return False, "CSV is missing one or more required columns: Entity, Type, Date, Filter"

    if df['Type'].isin(['Test', 'Not Test']).all() == False:
        return False, "Type column should only contain 'Test' or 'Not Test' values"

    try:
        pd.to_datetime(df['Date'], format='%m/%d/%Y')
    except ValueError:
        return False, "Date column should be in mm/dd/yyyy format"

    return True, "CSV is valid"


def find_twin_matches(df, weights, top_n):
    metrics = [col for col in df.columns if col not in ['Entity', 'Type', 'Date', 'Filter']]
    test_entities = df[df['Type'] == 'Test']['Entity'].unique()
    control_entities = df[df['Type'] == 'Not Test']['Entity'].unique()

    results = []
    top_n_results = []

    for test_entity in test_entities:
        test_data = df[df['Entity'] == test_entity]

        entity_results = []
        for control_entity in control_entities:
            if control_entity == test_entity:
                continue

            control_data = df[df['Entity'] == control_entity]

            if test_data['Filter'].iloc[0] != control_data['Filter'].iloc[0]:
                continue

            merged_data = pd.merge(test_data, control_data, on=['Date', 'Filter'], suffixes=('_test', '_control'))

            metric_ranks = {}
            for metric in metrics:
                differences = abs(merged_data[f'{metric}_test'] - merged_data[f'{metric}_control'])
                mean_diff = differences.mean()
                sd_diff = differences.std()
                score = mean_diff + sd_diff
                metric_ranks[metric] = score

            weighted_rank_sum = sum(metric_ranks[metric] * weights[metric] for metric in metrics)
            entity_results.append((control_entity, weighted_rank_sum, metric_ranks))

        entity_results.sort(key=lambda x: x[1])

        for rank, (control_entity, weighted_rank_sum, metric_ranks) in enumerate(entity_results, 1):
            results.append({
                'Test Entity': test_entity,
                'Twin Entity': control_entity,
                'Final Ranking': rank,
                **{f'{metric} Ranking': metric_ranks[metric] for metric in metrics}
            })

            if rank <= top_n:
                top_n_results.append({
                    'Test Entity': test_entity,
                    'Twin Entity': control_entity,
                    'Final Ranking': rank
                })

    return pd.DataFrame(results), pd.DataFrame(top_n_results)


st.header('Upload CSV File')
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Preview of uploaded data:")
    st.write(df.head())

    st.header('Validate CSV File Format')
    is_valid, message = validate_csv(df)
    if is_valid:
        st.success(message)
    else:
        st.error(message)
        st.stop()

    st.header('Enter Metric Weights')
    metrics = [col for col in df.columns if col not in ['Entity', 'Type', 'Date', 'Filter']]
    weights = {}
    for metric in metrics:
        weights[metric] = st.slider(f"Weight for {metric}", 0, 10, 5)

    st.header('Number of Control Stores')
    top_n = st.number_input("Number of control stores to find per test store", min_value=1, max_value=10, value=3)

    if st.button('Generate Control Stores'):
        st.header('Matching Results')
        detailed_results, top_n_results = find_twin_matches(df, weights, top_n)

        st.subheader("Top Control Stores")
        st.write(top_n_results)

        st.subheader("Detailed Results")
        st.write(detailed_results)

        st.header('Download Results')

        top_n_csv = top_n_results.to_csv(index=False)
        st.download_button(
            label="Download Top Control Stores",
            data=top_n_csv,
            file_name="top_control_stores.csv",
            mime="text/csv"
        )

        detailed_csv = detailed_results.to_csv(index=False)
        st.download_button(
            label="Download Detailed Results",
            data=detailed_csv,
            file_name="detailed_results.csv",
            mime="text/csv"
        )