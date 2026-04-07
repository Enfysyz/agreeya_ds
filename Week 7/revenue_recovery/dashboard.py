import joblib
import pandas as pd
from rich.console import Console
from rich.table import Table

from feature_store import FeatureStore

console = Console()

def generate_dashboard(pipeline_df, churn_threshold):
    console.print("\n[bold cyan]Dynamic Revenue Recovery Dashboard[/bold cyan]\n")
    
    # --- Calculate Pipeline Metrics ---
    total_tested = len(pipeline_df)
    
    # Count how many rows have a churn probability over our threshold
    predicted_churners = len(pipeline_df[pipeline_df['Churn_Prob'] > churn_threshold])
    
    # Summary Header
    console.print("[bold white]Daily Pipeline Summary[/bold white]")
    console.print(f" • Total Accounts Evaluated: [bold]{total_tested}[/bold]")
    console.print(f" • Accounts at Risk (> {churn_threshold * 100} % Prob): [bold red]{predicted_churners}[/bold red]\n")
    
    # --- Table Logic ---
    table = Table(show_header=True, header_style="bold white")
    table.add_column("Customer ID", width=15)
    table.add_column("Churn Probability", justify="right", style="yellow")
    table.add_column("Revenue at Risk", style="red bold", justify="right")
    
    total_risk = 0
    
    # Sort by highest Revenue at Risk
    pipeline_df['Risk_Amount'] = pipeline_df['Churn_Prob'] * pipeline_df['LTV']
    pipeline_df = pipeline_df.sort_values(by='Risk_Amount', ascending=False)
    
    for _, row in pipeline_df.iterrows():
        # Only show accounts that cross the At-Risk threshold
        if row['Churn_Prob'] > churn_threshold:
            risk_amount = row['LTV']
            total_risk += risk_amount
            table.add_row(
                str(row['CustomerID']),
                f"{row['Churn_Prob'] * 100:.1f}%",
                f"${risk_amount:,.2f}"
            )
            
    console.print(table)
    console.print(f"\n[bold red]Total Pipeline Revenue at Risk: ${total_risk:,.2f}[/bold red]\n")

if __name__ == "__main__":
    console.print("[dim]Loading model and fetching real-time pipeline data...[/dim]")
    
    # Feature Store to process the raw data 
    TRAIN_FILE = 'Week 7/revenue_recovery/data/customer_churn_dataset-training-master.csv'
    TEST_FILE = 'Week 7/revenue_recovery/data/customer_churn_dataset-testing-master.csv'
    MODEL_PATH = 'Week 7/revenue_recovery/output/revenue_risk_ensemble.pkl'
    
    # Load the trained model 
    model = joblib.load(MODEL_PATH)
    
    # Suppress print statements from FeatureStore if desired, or let them run
    store = FeatureStore(train_path=TRAIN_FILE, test_path=TEST_FILE)
    
    # Get the pre-processed test data
    _, X_test, _, _, test_customer_ids = store.get_train_test_splits(test_size=0.20)
    
    # Pick 50 random customers from the test set
    sample_indices = X_test.sample(n=50, random_state=None).index
    
    X_pipeline = X_test.loc[sample_indices]
    ids_pipeline = test_customer_ids.loc[sample_indices]
    
    # predict_proba returns [Probability of 0, Probability of 1]
    churn_probabilities = model.predict_proba(X_pipeline)[:, 1]
    
    # Map results to the Dashboard format
    pipeline_data = pd.DataFrame({
        'CustomerID': ids_pipeline,
        'Churn_Prob': churn_probabilities,
        'LTV': X_pipeline['LTV_Risk_12_Months'] 
    })
    
    # Render the Dashboard
    generate_dashboard(pipeline_data, 0.60)