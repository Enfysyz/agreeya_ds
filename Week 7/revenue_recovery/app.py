# streamlit run 'Week 7/revenue_recovery/app.py'

import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
from feature_store import FeatureStore
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(page_title="Revenue Recovery Hub", page_icon="📈", layout="wide")

# --- UI Polish (Custom CSS) ---
st.markdown("""
    <style>
    /* Global Spacing */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 95%; }
    h1, h2, h3 { color: #0f172a; font-weight: 600; }
    
    /* Metric Cards Styling */
    div[data-testid="stMetric"] { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 10px; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
        border: 1px solid #e2e8f0; 
        min-height: 140px; 
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        padding-bottom: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
        font-weight: 500;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        color: #0f172a;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("Dynamic Revenue Recovery Hub")
st.markdown("<p style='color: #64748b; font-size: 1.1rem;'>Upload your daily pipeline to identify at-risk accounts, analyze churn probability, and protect revenue.</p>", unsafe_allow_html=True)

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
    uploaded_file = st.file_uploader("Upload Pipeline CSV", type=["csv"], help="Must contain standard customer fields.")
    
    st.markdown("---")
    st.header("Model Settings")
    churn_threshold = st.slider("Action Threshold", 0.0, 1.0, 0.60, 0.05, 
                                help="Accounts above this probability will be flagged as 'At Risk'.")
    
    st.markdown("---")
    st.caption("Powered by RevenueRisk ML Model v1.2")

# --- Main Application Logic ---
if uploaded_file is not None:
    # 1. Process Data
    input_df = pd.read_csv(uploaded_file).dropna()
    processed_df = input_df.copy()
    processed_df = pd.get_dummies(processed_df, columns=['Gender', 'Subscription Type', 'Contract Length'], drop_first=True)
    
    processed_df['Tenure_Safe'] = processed_df['Tenure'].replace(0, 1) 
    processed_df['Monthly_Spend'] = processed_df['Total Spend'] / processed_df['Tenure_Safe']
    processed_df['LTV_Risk_12_Months'] = processed_df['Monthly_Spend'] * 12
    
    X_train_cols, _, _, _, _ = store.get_train_test_splits(test_size=0.20)
    expected_cols = X_train_cols.columns
    
    for col in expected_cols:
        if col not in processed_df.columns:
            processed_df[col] = 0
            
    X_inference = processed_df[expected_cols]

    # 2. Predict
    probs = model.predict_proba(X_inference)[:, 1]
    
    results_df = pd.DataFrame({
        'CustomerID': input_df['CustomerID'],
        'Churn_Prob': probs,
        'LTV': processed_df['LTV_Risk_12_Months']
    })
    results_df['Status'] = results_df['Churn_Prob'].apply(lambda x: 'At Risk' if x >= churn_threshold else 'Safe')
    
    # 3. Calculate KPIs
    total_tested = len(results_df)
    at_risk = len(results_df[results_df['Status'] == 'At Risk'])
    safe_accounts = total_tested - at_risk
    risk_rev = results_df[results_df['Status'] == 'At Risk']['LTV'].sum()
    total_rev = results_df['LTV'].sum()
    risk_percentage = (risk_rev / total_rev * 100) if total_rev > 0 else 0

    # --- Persistent Top KPI Row ---
    st.markdown("<br>", unsafe_allow_html=True) # Spacer
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Accounts Evaluated", f"{total_tested:,}")
    c2.metric("Safe Accounts", f"{safe_accounts:,}")
    c3.metric("Accounts at Risk", f"{at_risk:,}", delta=f"{(at_risk/total_tested)*100:.1f}% of pipeline", delta_color="inverse")
    c4.metric("Revenue at Risk", f"${risk_rev:,.0f}", delta=f"{risk_percentage:.1f}% of total LTV", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True) # Spacer

    # --- Tabbed Interface ---
    tab1, tab2, tab3 = st.tabs(["📊 Pipeline Health", "🚨 Priority Action List", "🔍 Customer Deep Dive"])

    # TAB 1: Overview Visuals
    with tab1:
        col_text, col_viz = st.columns([1, 2])
        with col_text:
            st.markdown("### Executive Summary")
            st.write(f"Based on the uploaded pipeline, **{at_risk}** accounts require immediate attention.")
            st.write(f"If action is not taken, there is a risk of losing **${risk_rev:,.0f}** in potential lifetime value over the next 12 months.")
                
        with col_viz:
            fig = px.pie(results_df, names='Status', hole=0.5, color='Status', 
                         color_discrete_map={'At Risk': '#ef4444', 'Safe': '#10b981'},
                         template='plotly_white')
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), showlegend=True, height=350)
            st.plotly_chart(fig, use_container_width=True)

    # TAB 2: Action List
    with tab2:
        st.markdown("### Top Accounts Requiring Intervention")
        st.write("Sorted by highest potential revenue impact.")
        risk_df = results_df[results_df['Status'] == 'At Risk'].sort_values(by='LTV', ascending=False)
        display_df = risk_df[['CustomerID', 'Churn_Prob', 'LTV']].copy()
        display_df.rename(columns={'LTV': 'Risk Amount', 'Churn_Prob': 'Probability of Churn'}, inplace=True)
        display_df['CustomerID'] = display_df['CustomerID'].astype(int).astype(str)
        display_df['Probability of Churn'] = (display_df['Probability of Churn'] * 100).apply(lambda x: f"{x:.1f}%")
        display_df['Risk Amount'] = display_df['Risk Amount'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

    # TAB 3: Customer Inspector
    with tab3:
        st.markdown("### Comparative Customer Inspector")
        st.write("Select a customer from the dropdown to see how their metrics compare against the rest of the pipeline.")
        
        customer_options = ["None"] + results_df['CustomerID'].astype(int).sort_values().tolist()
        selected_id = st.selectbox("Select Customer ID", customer_options)
        
        plot_df = input_df.copy()
        plot_df['Status'] = results_df['Status'].values
        plot_df['Grouping'] = "" 

        # Chart Helpers
        def create_strip_chart(df, column, title, cust_val=None, is_currency=False):
            fig = px.strip(df, x=column, y='Grouping', color='Status', hover_data=['CustomerID'], title=title, 
                           color_discrete_map={'At Risk': '#ef4444', 'Safe': '#10b981'}, template='plotly_white')
            fig.update_traces(marker=dict(size=8, opacity=0.6), jitter=1.0)
            
            if cust_val is not None:
                val_text = f"{cust_val:,.0f}" if is_currency else f"{cust_val}"
                fig.add_trace(go.Scatter(
                    x=[cust_val], y=[""], mode='markers+text',
                    marker=dict(color='#eab308', size=16, symbol='star', line=dict(color='#713f12', width=2)),
                    text=[f"Selected: {val_text}"], textposition="top center",
                    textfont=dict(color='#9ca3af', size=12), hoverinfo='skip', showlegend=False
                ))
            
            fig.update_layout(boxmode='overlay', margin=dict(t=40, b=10, l=10, r=10), 
                              yaxis=dict(showticklabels=False, title="", visible=False), 
                              xaxis_title="", showlegend=False)
            return fig

        def create_stacked_bar(df, column, title, cust_val=None):
            fig = px.histogram(df, x=column, color='Status', 
                               color_discrete_map={'At Risk': '#ef4444', 'Safe': '#10b981'},
                               template='plotly_white', barmode='stack')
            fig.update_traces(marker_line_width=1.5, marker_line_color='white', opacity=0.9)
            
            if cust_val is not None:
                if isinstance(cust_val, str):
                    fig.add_annotation(x=cust_val, y=1.0, yref="paper", yanchor="bottom", yshift=10, 
                                       text=f"Selected: {cust_val}", showarrow=True, arrowhead=2, 
                                       arrowsize=1, arrowwidth=2, arrowcolor="#eab308", font=dict(color="#9ca3af", size=12))
                else:
                    fig.add_vline(x=cust_val, line_width=3, line_dash="dash", line_color="#eab308",
                                  annotation_text=f"Selected: {cust_val}", annotation_position="top right",
                                  annotation_font=dict(color="#9ca3af", size=12))
            
            is_categorical = df[column].dtype == 'object'
            fig.update_layout(
                title=dict(text=title, y=0.98, yref="container", font=dict(color="#0f172a", size=15)), 
                margin=dict(t=90, b=10, l=10, r=10), yaxis_title="Count", xaxis_title="", showlegend=False, bargap=0.25,
                xaxis=dict(showgrid=False, categoryorder='total descending' if is_categorical else None), 
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9', zerolinecolor='#e2e8f0')
            )
            return fig

        # Handle Selection
        if selected_id != "None":
            cust_raw = input_df[input_df['CustomerID'] == selected_id].iloc[0]
            cust_results = results_df[results_df['CustomerID'] == selected_id].iloc[0]
            
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(f"#### 👤 Customer Profile: {selected_id}")
                
                # Expanded to 5 columns to include Revenue at Risk
                p1, p2, p3, p4, p5 = st.columns(5)
                
                p1.markdown(f"**Gender**<br>{cust_raw['Gender']}", unsafe_allow_html=True)
                p2.markdown(f"**Subscription**<br>{cust_raw['Subscription Type']}", unsafe_allow_html=True)
                p3.markdown(f"**Contract**<br>{cust_raw['Contract Length']}", unsafe_allow_html=True)
                
                # Churn Probability Formatting
                prob = cust_results['Churn_Prob'] * 100
                is_at_risk = prob >= (churn_threshold * 100)
                status_color = "red" if is_at_risk else "green"
                
                p4.markdown(f"**Predicted Churn**<br>:{status_color}[**{prob:.1f}%**]", unsafe_allow_html=True)
                
                # NEW: Revenue at Risk Metric
                # We show the value in red if they are at risk to emphasize the potential loss
                risk_val = cust_results['LTV']
                p5.markdown(
                    f"**Revenue at Risk**<br>:{status_color}[**${risk_val:,.2f}**]", 
                    unsafe_allow_html=True,
                    help="Calculated based on 12-month projected Lifetime Value (LTV)."
                )
                
                # Full Record Expander (from previous step)
                with st.expander("📋 View Full Customer Record"):
                    full_record_df = pd.DataFrame(cust_raw).reset_index()
                    full_record_df.columns = ['Attribute', 'Value']
                    st.dataframe(full_record_df, hide_index=True, use_container_width=True)
                    
            st.markdown("<br>", unsafe_allow_html=True)
                
            val_spend, val_calls, val_age = cust_raw['Total Spend'], cust_raw['Support Calls'], cust_raw['Age']
            val_delay, val_gender, val_contract = cust_raw['Payment Delay'], cust_raw['Gender'], cust_raw['Contract Length']
        else:
            val_spend = val_calls = val_age = val_delay = val_gender = val_contract = None

        # Render Grid
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.plotly_chart(create_strip_chart(plot_df, 'Total Spend', "Total Spend Distribution", val_spend, True), use_container_width=True)
            st.plotly_chart(create_stacked_bar(plot_df, 'Support Calls', "Support Calls", val_calls), use_container_width=True)
            st.plotly_chart(create_stacked_bar(plot_df, 'Gender', "Gender", val_gender), use_container_width=True)
            
        with chart_col2:
            st.plotly_chart(create_strip_chart(plot_df, 'Age', "Age Distribution", val_age), use_container_width=True)
            st.plotly_chart(create_stacked_bar(plot_df, 'Payment Delay', "Payment Delay (Days)", val_delay), use_container_width=True)
            st.plotly_chart(create_stacked_bar(plot_df, 'Contract Length', "Contract Length", val_contract), use_container_width=True)

else:
    # --- Professional Empty State ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.info("👋 **Welcome to the Revenue Recovery Hub**")
        st.markdown("""
        To begin your analysis, please upload your daily pipeline CSV via the sidebar menu. 
        """)