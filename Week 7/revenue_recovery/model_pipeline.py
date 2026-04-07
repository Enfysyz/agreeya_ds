import optuna
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import cross_val_score
import warnings

warnings.filterwarnings('ignore')

def optimize_and_train(X, y):
    def objective(trial):
        # Hyperparameters for Random Forest
        rf_n_estimators = trial.suggest_int('rf_n_estimators', 50, 150)
        rf_max_depth = trial.suggest_int('rf_max_depth', 3, 6) # Capped at 6 to prevent overfitting
        
        # Hyperparameters for XGBoost
        xgb_learning_rate = trial.suggest_float('xgb_learning_rate', 1e-3, 0.05, log=True) # Lower max rate
        xgb_max_depth = trial.suggest_int('xgb_max_depth', 3, 5) # Capped at 5
        
        # Instantiate models
        rf = RandomForestClassifier(
            n_estimators=rf_n_estimators, 
            max_depth=rf_max_depth, 
            class_weight='balanced', # Automatically handles churn class imbalance
            random_state=42
        )
        xgb = XGBClassifier(
            learning_rate=xgb_learning_rate, 
            max_depth=xgb_max_depth, 
            eval_metric='logloss', 
            random_state=42
        )
        
        # Create Ensemble
        ensemble = VotingClassifier(estimators=[('rf', rf), ('xgb', xgb)], voting='soft')
        
        # Optimizing for F1-Score
        score = cross_val_score(ensemble, X, y, cv=3, scoring='f1').mean()
        return score

    # Run Optuna Study
    print("--- Starting Optuna hyperparameter tuning ---")
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=10)
    
    print(f"\n--- Best trial F1-Score: {study.best_value:.4f} ---")
    
    # Train final model with best params
    best_rf = RandomForestClassifier(
        n_estimators=study.best_params['rf_n_estimators'], 
        max_depth=study.best_params['rf_max_depth'],
        class_weight='balanced',
        random_state=42
    )
    best_xgb = XGBClassifier(
        learning_rate=study.best_params['xgb_learning_rate'], 
        max_depth=study.best_params['xgb_max_depth'],
        eval_metric='logloss',
        random_state=42
    )
    
    final_ensemble = VotingClassifier(estimators=[('rf', best_rf), ('xgb', best_xgb)], voting='soft')
    final_ensemble.fit(X, y)
    
    return final_ensemble