# streamlit run 'Week 7/revenue_recovery/app.py'
import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
import os
from feature_store import FeatureStore

# --- 1. Page Configuration ---
st.set_page_config(page_title="Revenue Recovery Dashboard", page_icon="💸", layout="wide")
st.title("Dynamic Revenue Recovery Dashboard")
st.markdown("Identify high-risk accounts and protect pipeline revenue using machine learning.")

# --- 2. Load Model & Data (Cached for speed) ---
@st.cache_resource
def load_ml_assets():
    # Load Model
    model_path = 'Week 7/revenue_recovery/output/revenue_risk_ensemble.pkl'
    model = joblib.load(model_path)
    
    # Load Feature Store (To ensure data is preprocessed exactly like training)
    train_file = 'Week 7/revenue_recovery/data/customer_churn_dataset-training-master.csv'
    test_file = 'Week 7/revenue_recovery/data/customer_churn_dataset-testing-master.csv'
    store = FeatureStore(train_path=train_file, test_path=test_file)
    
    return model, store

try:
    model, store = load_ml_assets()
except Exception as e:
    st.error(f"Error loading assets. Please check your file paths. Details: {e}")
    st.stop()

# --- 3. Sidebar Controls ---
st.sidebar.header("Pipeline Settings")

# Simulate a dropdown of available daily pipeline files
# In a real scenario, this could read os.listdir('data/pipelines/')
pipeline_options = ["Daily_Batch_A.csv", "Daily_Batch_B.csv", "Daily_Batch_C.csv"]
selected_pipeline = st.sidebar.selectbox("Select Pipeline CSV to Analyze", pipeline_options)

# Threshold Slider
st.sidebar.markdown("---")
churn_threshold = st.sidebar.slider(
    "Decision Threshold (Churn Probability)", 
    min_value=0.0, max_value=1.0, value=0.60, step=0.05,
    help="Increase this to only see the absolute highest-risk accounts. Decrease to cast a wider net."
)

# --- 4. Process Data based on Selection ---
# To simulate different CSVs while ensuring columns match your model perfectly, 
# we will draw different random samples from your preprocessed test set.
_, X_test, _, _, test_customer_ids = store.get_train_test_splits(test_size=0.20)

# Simulate different files mapping to different random seeds
seed_map = {"Daily_Batch_A.csv": 42, "Daily_Batch_B.csv": 100, "Daily_Batch_C.csv": 999}
sample_indices = X_test.sample(n=150, random_state=seed_map[selected_pipeline]).index

X_pipeline = X_test.loc[sample_indices]
ids_pipeline = test_customer_ids.loc[sample_indices]

# Run Predictions
churn_probabilities = model.predict_proba(X_pipeline)[:, 1]

# Create Pipeline DataFrame
pipeline_df = pd.DataFrame({
    'CustomerID': ids_pipeline,
    'Churn_Prob': churn_probabilities,
    'LTV': X_pipeline['LTV_Risk_12_Months']
})

# Apply threshold logic
pipeline_df['Status'] = pipeline_df['Churn_Prob'].apply(lambda x: 'At Risk' if x >= churn_threshold else 'Safe')
pipeline_df['Risk_Amount'] = pipeline_df.apply(lambda row: row['LTV'] if row['Status'] == 'At Risk' else 0, axis=1)

# --- 5. Top Level Metrics ---
total_tested = len(pipeline_df)
predicted_churners = len(pipeline_df[pipeline_df['Status'] == 'At Risk'])
predicted_stayers = total_tested - predicted_churners
total_revenue_risk = pipeline_df['Risk_Amount'].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Accounts Evaluated", total_tested)
col2.metric("Accounts at Risk", predicted_churners, delta_color="inverse")
col3.metric("Safe Accounts", predicted_stayers)
col4.metric("Total Revenue at Risk", f"${total_revenue_risk:,.2f}")

st.markdown("---")

# --- 6. Visualizations & Data Table ---
col_viz, col_table = st.columns([1, 2])

with col_viz:
    st.subheader("Pipeline Distribution")
    # Interactive Pie Chart using Plotly
    pie_data = pd.DataFrame({'Status': ['At Risk', 'Safe'], 'Count': [predicted_churners, predicted_stayers]})
    fig = px.pie(
        pie_data, values='Count', names='Status', hole=0.4, 
        color='Status', color_discrete_map={'At Risk': '#ef4444', 'Safe': '#22c55e'}
    )
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.subheader("High-Risk Accounts Action List")
    # Filter for only at-risk accounts, sort by LTV impact, and format for display
    risk_df = pipeline_df[pipeline_df['Status'] == 'At Risk'].sort_values(by='Risk_Amount', ascending=False)
    
    display_df = risk_df[['CustomerID', 'Churn_Prob', 'Risk_Amount']].copy()
    display_df['Churn_Prob'] = (display_df['Churn_Prob'] * 100).apply(lambda x: f"{x:.1f}%")
    display_df['Risk_Amount'] = display_df['Risk_Amount'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("---")

# --- 7. Deep Dive: Customer Inspector ---
st.header("🔍 Customer Deep Dive")
st.markdown("Select a Customer ID to view their full profile and behavioral metrics.")

# Dropdown to select a customer from the current pipeline
selected_id = st.selectbox("Search Customer ID", pipeline_df['CustomerID'].astype(int).sort_values())

if selected_id:
    # THE FIX: Load and combine BOTH raw datasets since our split mixed them
    raw_train = pd.read_csv('Week 7/revenue_recovery/data/customer_churn_dataset-training-master.csv')
    raw_test = pd.read_csv('Week 7/revenue_recovery/data/customer_churn_dataset-testing-master.csv')
    raw_df = pd.concat([raw_train, raw_test], axis=0)
    
    # Safely match the ID (forcing both to float just in case of formatting issues)
    customer_match = raw_df[raw_df['CustomerID'] == float(selected_id)]
    
    # Safety Check: Make sure the customer actually exists before pulling .iloc[0]
    if not customer_match.empty:
        raw_customer_data = customer_match.iloc[0]
        prob = pipeline_df[pipeline_df['CustomerID'] == selected_id]['Churn_Prob'].values[0]
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info(f"**Age:** {raw_customer_data['Age']}\n\n**Gender:** {raw_customer_data['Gender']}")
        with c2:
            st.warning(f"**Support Calls:** {raw_customer_data['Support Calls']}\n\n**Payment Delays:** {raw_customer_data['Payment Delay']}")
        with c3:
            st.success(f"**Predicted Churn:** {prob * 100:.1f}%\n\n**Total Spend:** ${raw_customer_data['Total Spend']:,.2f}")
    else:
        st.error(f"Could not locate Customer ID {selected_id} in the raw datasets.")