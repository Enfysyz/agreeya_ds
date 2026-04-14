# generate_sample.py
import pandas as pd

# Load your raw data
TRAIN_PATH = 'Week 7/revenue_recovery/data/customer_churn_dataset-training-master.csv'
TEST_PATH = 'Week 7/revenue_recovery/data/customer_churn_dataset-testing-master.csv'

df_train = pd.read_csv(TRAIN_PATH)
df_test = pd.read_csv(TEST_PATH)

# Combine them
df_master = pd.concat([df_train, df_test], axis=0)

# Randomly sample 150 rows
sample_df = df_master.sample(n=1000)
sample_df = sample_df.drop(columns=['Churn'])

# Save to a new CSV
OUTPUT_PATH = 'Week 7/revenue_recovery/data/sample_pipeline1.csv'
sample_df.to_csv(OUTPUT_PATH, index=False)
print("Created 'sample_pipeline.csv' with 150 random customers.")