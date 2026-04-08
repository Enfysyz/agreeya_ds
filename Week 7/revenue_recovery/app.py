#  streamlit run 'Week 7/revenue_recovery/app.py'

import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
from feature_store import FeatureStore
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(page_title="Revenue Recovery Hub", page_icon="📈", layout="wide")

# Custom CSS for a cleaner, professional look
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1, h2, h3 { color: #0f172a; }
    
    div[data-testid="stMetric"] { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 8px; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
        border: 1px solid #e2e8f0; 
        min-height: 135px; /* THE FIX: Forces all metric boxes to be the exact same height */
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Dynamic Revenue Recovery Hub")
st.markdown("Upload your daily pipeline to identify at-risk accounts, analyze churn probability, and protect revenue.")

# --- Load ML Assets ---
@st.cache_resource
def load_ml_assets():
    model = joblib.load('Week 7/revenue_recovery/output/revenue_risk_ensemble.pkl')
    store = FeatureStore(
        train_path='Week 7/revenue_recovery/data/customer_churn_dataset-training-master.csv',
        test_path='Week 7/revenue_recovery/data/customer_churn_dataset-testing-master.csv'
    )
    return model, store

model, store = load_ml_assets()

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("Data Ingestion")
    uploaded_file = st.file_uploader("Upload Pipeline CSV", type=["csv"])
    st.markdown("---")
    st.header("Model Settings")
    churn_threshold = st.slider("Action Threshold", 0.0, 1.0, 0.60, 0.05, 
                                help="Accounts above this probability will be flagged as 'At Risk'.")

# --- Main Application Logic ---
if uploaded_file is not None:
    input_df = pd.read_csv(uploaded_file).dropna()
    
    # Preprocessing
    processed_df = input_df.copy()
    processed_df = pd.get_dummies(processed_df, columns=['Gender', 'Subscription Type', 'Contract Length'], drop_first=True)
    
    processed_df['Tenure_Safe'] = processed_df['Tenure'].replace(0, 1) 
    processed_df['Monthly_Spend'] = processed_df['Total Spend'] / processed_df['Tenure_Safe']
    processed_df['LTV_Risk_12_Months'] = processed_df['Monthly_Spend'] * 12
    
    # Column Alignment
    X_train_cols, _, _, _, _ = store.get_train_test_splits(test_size=0.20)
    expected_cols = X_train_cols.columns
    
    for col in expected_cols:
        if col not in processed_df.columns:
            processed_df[col] = 0
            
    X_inference = processed_df[expected_cols]

    # Predictions
    probs = model.predict_proba(X_inference)[:, 1]
    
    results_df = pd.DataFrame({
        'CustomerID': input_df['CustomerID'],
        'Churn_Prob': probs,
        'LTV': processed_df['LTV_Risk_12_Months']
    })
    results_df['Status'] = results_df['Churn_Prob'].apply(lambda x: 'At Risk' if x >= churn_threshold else 'Safe')
    
    # Metrics Calculation
    total_tested = len(results_df)
    at_risk = len(results_df[results_df['Status'] == 'At Risk'])
    safe_accounts = total_tested - at_risk
    risk_rev = results_df[results_df['Status'] == 'At Risk']['LTV'].sum()
    total_rev = results_df['LTV'].sum()
    risk_percentage = (risk_rev / total_rev * 100) if total_rev > 0 else 0

    # --- Top KPI Row ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Accounts Evaluated", total_tested)
    c2.metric("Safe Accounts", safe_accounts)
    c3.metric("Accounts at Risk", at_risk, delta=f"{(at_risk/total_tested)*100:.1f}% of pipeline", delta_color="inverse")
    c4.metric("Revenue at Risk", f"${risk_rev:,.0f}", delta=f"{risk_percentage:.1f}% of total LTV", delta_color="inverse")

    # st.markdown("---")

    # --- Visuals & Action List ---
    col_viz, col_table = st.columns([1, 1.5])
    
    with col_viz:
        st.subheader("Pipeline Health")
        fig = px.pie(results_df, names='Status', hole=0.5, color='Status', 
                     color_discrete_map={'At Risk': '#ef4444', 'Safe': '#10b981'},
                     template='plotly_white')
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.subheader("Priority Action List")
        risk_df = results_df[results_df['Status'] == 'At Risk'].sort_values(by='LTV', ascending=False)
        display_df = risk_df[['CustomerID', 'Churn_Prob', 'LTV']].copy()
        display_df.rename(columns={'LTV': 'Risk Amount'}, inplace=True)
        display_df['CustomerID'] = display_df['CustomerID'].astype(int).astype(str)
        display_df['Churn_Prob'] = (display_df['Churn_Prob'] * 100).apply(lambda x: f"{x:.1f}%")
        display_df['Risk Amount'] = display_df['Risk Amount'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    # st.markdown("---")

    # --- Customer Deep Dive (The Highlight Feature) ---
    st.subheader("Comparative Customer Inspector")
    st.markdown("View overall pipeline distributions, or select a customer to see how their behavior compares.")
    
    # 1. Add "None" to the start of the dropdown options
    customer_options = ["None"] + results_df['CustomerID'].astype(int).sort_values().tolist()
    selected_id = st.selectbox("Select Customer ID", customer_options)
    
    # 2. Prepare data for plotting (Happens ALWAYS, regardless of selection)
    plot_df = input_df.copy()
    plot_df['Status'] = results_df['Status'].values
    plot_df['Grouping'] = "" # Dummy column for strip plot alignment

    # 3. Updated Helper Functions (Now handle 'None' gracefully)
    def create_strip_chart(df, column, title, cust_val=None, is_currency=False):
        fig = px.strip(df, x=column, y='Grouping', color='Status', hover_data=['CustomerID'], title=title, 
                       color_discrete_map={'At Risk': '#ef4444', 'Safe': '#10b981'},
                       template='plotly_white')
        
        fig.update_traces(marker=dict(size=8, opacity=0.6), jitter=1.0)
        
        # Only draw the golden star if a customer value exists
        if cust_val is not None:
            val_text = f"{cust_val:,.0f}" if is_currency else f"{cust_val}"
            fig.add_trace(go.Scatter(
                x=[cust_val], 
                y=[""], 
                mode='markers+text',
                marker=dict(color='#eab308', size=16, symbol='star', line=dict(color='#713f12', width=2)),
                text=[f"Selected: {val_text}"],
                textposition="top center",
                textfont=dict(color='#9ca3af', size=12),
                hoverinfo='skip',
                showlegend=False
            ))
        
        fig.update_layout(
            boxmode='overlay', 
            margin=dict(t=40, b=10, l=10, r=10), 
            yaxis=dict(showticklabels=False, title="", visible=False), 
            xaxis_title="",
            showlegend=False
        )
        return fig

    def create_stacked_bar(df, column, title, cust_val=None):
        fig = px.histogram(df, x=column, color='Status', title=title,
                           color_discrete_map={'At Risk': '#ef4444', 'Safe': '#10b981'},
                           template='plotly_white', barmode='stack')
        
        # Only draw the golden line if a customer value exists
        if cust_val is not None:
            fig.add_vline(x=cust_val, line_width=3, line_dash="dash", line_color="#eab308",
                          annotation_text=f"Selected: {cust_val}", 
                          annotation_position="top right",
                          annotation_font=dict(color="#9ca3af"))
        
        fig.update_layout(
            margin=dict(t=40, b=10, l=10, r=10), 
            yaxis_title="Number of Customers", 
            xaxis_title="",
            showlegend=False
        )
        return fig

    # 4. Handle Selection Logic
    if selected_id != "None":
        # Extract specific customer data
        cust_raw = input_df[input_df['CustomerID'] == selected_id].iloc[0]
        cust_results = results_df[results_df['CustomerID'] == selected_id].iloc[0]
        
        # Show Profile Card
        with st.container(border=True):
            st.markdown(f"#### Customer Profile: {selected_id}")
            p1, p2, p3, p4 = st.columns(4)
            p1.markdown(f"**Gender**\n\n{cust_raw['Gender']}")
            p2.markdown(f"**Subscription**\n\n{cust_raw['Subscription Type']}")
            p3.markdown(f"**Contract**\n\n{cust_raw['Contract Length']}")
            
            prob = cust_results['Churn_Prob'] * 100
            color = "red" if prob >= (churn_threshold * 100) else "green"
            p4.markdown(f"**Predicted Churn**\n\n:{color}[**{prob:.1f}%**]")
            
        # Assign values for highlighting
        val_spend = cust_raw['Total Spend']
        val_calls = cust_raw['Support Calls']
        val_age = cust_raw['Age']
        val_delay = cust_raw['Payment Delay']
    else:
        # If "None" is selected, pass None to the charts
        val_spend = val_calls = val_age = val_delay = None

    # 5. Always Draw the Charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.plotly_chart(create_strip_chart(plot_df, 'Total Spend', "Total Spend Distribution", val_spend, True), use_container_width=True)
        st.plotly_chart(create_stacked_bar(plot_df, 'Support Calls', "Support Calls Distribution", val_calls), use_container_width=True)
        
    with chart_col2:
        st.plotly_chart(create_strip_chart(plot_df, 'Age', "Age Distribution", val_age), use_container_width=True)
        st.plotly_chart(create_stacked_bar(plot_df, 'Payment Delay', "Payment Delay (Days) Distribution", val_delay), use_container_width=True)
else:
    # Empty state when no file is uploaded
    st.info("Upload a pipeline CSV file in the sidebar to begin your analysis")