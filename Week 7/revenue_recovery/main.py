# main.py
import os
import joblib
import pandas as pd
from feature_store import FeatureStore
from model_pipeline import optimize_and_train
from sklearn.metrics import classification_report

# Initialize Feature Store 
TRAIN_FILE = 'Week 7/revenue_recovery/data/customer_churn_dataset-training-master.csv'
TEST_FILE = 'Week 7/revenue_recovery/data/customer_churn_dataset-testing-master.csv'
OUTPUT_DIR = 'Week 7/revenue_recovery/output'

store = FeatureStore(train_path=TRAIN_FILE, test_path=TEST_FILE)


X_train, X_test, y_train, y_test, test_customer_ids = store.get_train_test_splits(test_size=0.20)

# Train the Model 
model = optimize_and_train(X_train, y_train)

# Evaluate 
print("\n--- Evaluating Model on 20% Test Set ---")
predictions = model.predict(X_test)
report = classification_report(y_test, predictions)
print(report)

# Feature Importances
xgb_model = model.named_estimators_['xgb']
feature_importances = pd.Series(xgb_model.feature_importances_, index=X_train.columns)

print("\nTop 5 Most Important Features:")
print(feature_importances.sort_values(ascending=False).head(5))
print("-" * 50)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Save the Trained Model
model_path = os.path.join(OUTPUT_DIR, 'revenue_risk_ensemble.pkl')
joblib.dump(model, model_path)
print(f"Model saved to: {model_path}")

# Save the Classification Report 
report_path = os.path.join(OUTPUT_DIR, 'classification_report.txt')
with open(report_path, 'w') as f:
    f.write("Revenue-at-Risk Model Evaluation\n")
    f.write("================================\n")
    f.write(report)
print(f"Evaluation report saved to: {report_path}")

# Feature Importances as a CSV
importance_path = os.path.join(OUTPUT_DIR, 'feature_importances.csv')
feature_importances.sort_values(ascending=False).to_csv(importance_path, header=['Importance'])
print(f"Feature importances saved to: {importance_path}")
