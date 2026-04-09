# feature_store.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

class FeatureStore:
    def __init__(self, train_path, test_path):
        
        print("--- Concatenating datasets ---")
        df_train = pd.read_csv(train_path)
        df_test = pd.read_csv(test_path)
        
        self.data = pd.concat([df_train, df_test], axis=0)
        self.data.reset_index(drop=True, inplace=True)
        
        
        self.data = self.data.dropna()
        
        
        print("--- Preprocessing features ---")
        self._preprocess()
        
    def _preprocess(self):
        
        categorical_cols = ['Gender', 'Subscription Type', 'Contract Length']
        self.data = pd.get_dummies(self.data, columns=categorical_cols, drop_first=True)
        
        # Calculate LTV
        self.data['Tenure_Safe'] = self.data['Tenure'].replace(0, 1) 
        self.data['Monthly_Spend'] = self.data['Total Spend'] / self.data['Tenure_Safe']
        self.data['LTV_Risk_12_Months'] = self.data['Monthly_Spend'] * 12
        
    def get_train_test_splits(self, test_size=0.20):
        
        cols_to_drop = ['CustomerID', 'Churn', 'Tenure_Safe']
        X = self.data.drop(columns=cols_to_drop)
        y = self.data['Churn']
        customer_ids = self.data['CustomerID']

        X_train, X_test, y_train, y_test, ids_train, ids_test = train_test_split(
            X, y, customer_ids, 
            test_size=test_size, 
            random_state=42, 
            stratify=y 
        )
        
        return X_train, X_test, y_train, y_test, ids_test