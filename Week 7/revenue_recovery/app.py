import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
from feature_store import FeatureStore

st.set_page_config(page_title="Revenue Recovery Dashboard", page_icon="💸", layout="wide")
st.title("💸 Dynamic Revenue Recovery Dashboard")

@st.cache_resource
def load_ml_assets():
    model = joblib.load('Week 7/revenue_recovery/output/revenue_risk_ensemble.pkl')
    # Use the existing store to get the "correct" column structure from training
    store = FeatureStore(
        train_path='Week 7/revenue_recovery/data/customer_churn_dataset-training-master.csv',
        test_path='Week 7/revenue_recovery/data/customer_churn_dataset-testing-master.csv'
    )
    return model, store

model, store = load_ml_assets()

# --- Sidebar: File Upload ---
st.sidebar.header("📥 Data Ingestion")
uploaded_file = st.sidebar.file_uploader("Upload Pipeline CSV", type=["csv"])

churn_threshold = st.sidebar.slider("Decision Threshold", 0.0, 1.0, 0.60, 0.05)

if uploaded_file is not None:
    # 1. Load the uploaded data
    input_df = pd.read_csv(uploaded_file).dropna()
    
    # 2. Preprocess using the SAME logic as the FeatureStore
    processed_df = input_df.copy()
    processed_df = pd.get_dummies(processed_df, columns=['Gender', 'Subscription Type', 'Contract Length'], drop_first=True)
    
    # Calculate LTV features
    processed_df['Tenure_Safe'] = processed_df['Tenure'].replace(0, 1) 
    processed_df['Monthly_Spend'] = processed_df['Total Spend'] / processed_df['Tenure_Safe']
    processed_df['LTV_Risk_12_Months'] = processed_df['Monthly_Spend'] * 12
    
    # --- CRITICAL: Column Alignment ---
    X_train_cols, _, _, _, _ = store.get_train_test_splits()
    expected_cols = X_train_cols.columns
    
    # Add missing columns with 0s, and remove extra columns
    for col in expected_cols:
        if col not in processed_df.columns:
            processed_df[col] = 0
            
    X_inference = processed_df[expected_cols]

    # 3. Predict
    probs = model.predict_proba(X_inference)[:, 1]
    
    # 4. Results DataFrame
    results_df = pd.DataFrame({
        'CustomerID': input_df['CustomerID'],
        'Churn_Prob': probs,
        'LTV': processed_df['LTV_Risk_12_Months']
    })
    
    results_df['Status'] = results_df['Churn_Prob'].apply(lambda x: 'At Risk' if x >= churn_threshold else 'Safe')
    
    # --- Display Metrics ---
    total_tested = len(results_df)
    at_risk = len(results_df[results_df['Status'] == 'At Risk'])
    safe_accounts = total_tested - at_risk  # Calculated Safe Accounts
    risk_rev = results_df[results_df['Status'] == 'At Risk']['LTV'].sum()
    
    # Changed to 4 columns to include Safe Accounts
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Evaluated", total_tested)
    c2.metric("At Risk", at_risk, delta_color="inverse")
    c3.metric("Safe Accounts", safe_accounts)
    c4.metric("Revenue at Risk", f"${risk_rev:,.2f}")

    st.markdown("---")

    # --- Visuals & Action List ---
    col_viz, col_table = st.columns([1, 2])
    
    with col_viz:
        st.subheader("Pipeline Analysis")
        fig = px.pie(results_df, names='Status', hole=0.4, color='Status', 
                     color_discrete_map={'At Risk': '#ef4444', 'Safe': '#22c55e'})
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.subheader("🚨 High-Risk Accounts Action List")
        # Filter for at-risk accounts and sort by highest financial impact
        risk_df = results_df[results_df['Status'] == 'At Risk'].sort_values(by='LTV', ascending=False)
        
        # Format the dataframe for a clean UI presentation
        display_df = risk_df[['CustomerID', 'Churn_Prob', 'LTV']].copy()
        display_df.rename(columns={'LTV': 'Risk_Amount'}, inplace=True)
        
        display_df['CustomerID'] = display_df['CustomerID'].astype(int).astype(str) # Remove decimals from ID
        display_df['Churn_Prob'] = (display_df['Churn_Prob'] * 100).apply(lambda x: f"{x:.1f}%")
        display_df['Risk_Amount'] = display_df['Risk_Amount'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # --- Customer Search ---
    st.subheader("🔍 Individual Search")
    selected_id = st.selectbox("View Details for Customer", results_df['CustomerID'].astype(int))
    if selected_id:
        cust_row = input_df[input_df['CustomerID'] == selected_id].iloc[0]
        st.write(cust_row)

else:
    st.info("Please upload a CSV file in the sidebar to begin analysis.")