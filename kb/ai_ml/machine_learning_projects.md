---
tags: [machine-learning, ml, scikit-learn, tensorflow, keras, model-training, feature-engineering]
persona: ml
---

# Machine Learning Projects & Krishna's Real-World Experience

## Predictive Analytics at Walgreens

### Customer Churn Prediction Model
**Krishna's Implementation:**
So at Walgreens, I built this customer churn prediction model that actually helped reduce churn by about 15%. What I did was use historical transaction data - we're talking like 2 years of customer purchases, prescription refills, and loyalty program activity.

**Feature Engineering:**
```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

def engineer_customer_features(df):
    """
    Create features for churn prediction
    This is what I used in production at Walgreens
    """
    # Recency, Frequency, Monetary features
    customer_features = df.groupby('customer_id').agg({
        'order_date': lambda x: (pd.Timestamp.now() - x.max()).days,  # Recency
        'order_id': 'count',  # Frequency
        'amount': ['sum', 'mean', 'std']  # Monetary
    })
    
    customer_features.columns = ['recency', 'frequency', 'total_spent', 'avg_order', 'order_std']
    
    # Engagement features - these actually helped a lot
    customer_features['days_since_first_order'] = df.groupby('customer_id')['order_date'].apply(
        lambda x: (x.max() - x.min()).days
    )
    
    # Purchase patterns
    customer_features['purchase_frequency'] = customer_features['frequency'] / (
        customer_features['days_since_first_order'] + 1
    )
    
    # Trend features - is customer spending increasing or decreasing?
    recent_30_days = df[df['order_date'] >= pd.Timestamp.now() - pd.Timedelta(days=30)]
    customer_features['recent_orders'] = recent_30_days.groupby('customer_id').size()
    customer_features['recent_orders'] = customer_features['recent_orders'].fillna(0)
    
    return customer_features

# Load and prepare data
transactions = pd.read_csv('customer_transactions.csv', parse_dates=['order_date'])
features = engineer_customer_features(transactions)

# Create target variable - churned if no purchase in 90 days
features['churned'] = (features['recency'] > 90).astype(int)

# Handle missing values
features = features.fillna(0)

print(f"Total customers: {len(features)}")
print(f"Churn rate: {features['churned'].mean():.2%}")
```

**Model Training:**
```python
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import matplotlib.pyplot as plt

# Split data
X = features.drop(['churned'], axis=1)
y = features['churned']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Try multiple models - I found Random Forest worked best
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42)
}

results = {}
for name, model in models.items():
    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    results[name] = {
        'model': model,
        'accuracy': model.score(X_test_scaled, y_test),
        'roc_auc': roc_auc_score(y_test, y_pred_proba)
    }
    
    print(f"\n{name} Results:")
    print(f"Accuracy: {results[name]['accuracy']:.3f}")
    print(f"ROC-AUC: {results[name]['roc_auc']:.3f}")
    print(classification_report(y_test, y_pred))

# Random Forest won with 0.87 AUC
best_model = results['Random Forest']['model']
```

**Feature Importance Analysis:**
```python
import matplotlib.pyplot as plt

# What I learned was that recency and purchase frequency were the top predictors
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': best_model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nTop 10 Most Important Features:")
print(feature_importance.head(10))

# Plot feature importance
plt.figure(figsize=(10, 6))
plt.barh(feature_importance['feature'][:10], feature_importance['importance'][:10])
plt.xlabel('Importance')
plt.title('Top 10 Feature Importance')
plt.tight_layout()
plt.savefig('feature_importance.png')
```

## Demand Forecasting for Pharmacy Inventory

### Time Series Forecasting
**Krishna's Approach:**
So we had this problem where some pharmacies were running out of stock while others had too much inventory. I built a forecasting model using historical sales data and it actually reduced stockouts by 30%.

```python
import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error, mean_squared_error

def forecast_product_demand(product_id, store_id, historical_data):
    """
    Forecast demand for next 30 days
    Used this in production for 200+ stores
    """
    # Filter data for specific product and store
    df = historical_data[
        (historical_data['product_id'] == product_id) & 
        (historical_data['store_id'] == store_id)
    ].copy()
    
    # Create daily time series
    df = df.set_index('date').resample('D')['quantity_sold'].sum()
    df = df.fillna(0)  # Days with no sales
    
    # Handle outliers - sometimes we had data entry errors
    Q1 = df.quantile(0.25)
    Q3 = df.quantile(0.75)
    IQR = Q3 - Q1
    df = df.clip(lower=Q1 - 1.5*IQR, upper=Q3 + 1.5*IQR)
    
    # Split train/test
    train_size = int(len(df) * 0.8)
    train, test = df[:train_size], df[train_size:]
    
    # SARIMA model - seasonal pattern was weekly
    try:
        model = SARIMAX(
            train,
            order=(1, 1, 1),  # ARIMA parameters
            seasonal_order=(1, 1, 1, 7),  # Weekly seasonality
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        
        fitted_model = model.fit(disp=False)
        
        # Forecast
        forecast = fitted_model.forecast(steps=len(test))
        
        # Calculate metrics
        mae = mean_absolute_error(test, forecast)
        rmse = np.sqrt(mean_squared_error(test, forecast))
        
        # Forecast next 30 days
        future_forecast = fitted_model.forecast(steps=30)
        
        return {
            'forecast': future_forecast,
            'mae': mae,
            'rmse': rmse,
            'model': fitted_model
        }
    
    except Exception as e:
        print(f"Error forecasting for product {product_id}, store {store_id}: {e}")
        # Fallback to simple moving average
        return {
            'forecast': train.rolling(window=7).mean().iloc[-1],
            'mae': None,
            'rmse': None,
            'model': None
        }

# Run forecasting for all products
products = historical_data[['product_id', 'store_id']].drop_duplicates()

forecasts = []
for _, row in products.iterrows():
    result = forecast_product_demand(row['product_id'], row['store_id'], historical_data)
    forecasts.append({
        'product_id': row['product_id'],
        'store_id': row['store_id'],
        'forecast': result['forecast'],
        'mae': result['mae']
    })

forecasts_df = pd.DataFrame(forecasts)
print(f"Generated forecasts for {len(forecasts_df)} product-store combinations")
```

## Recommendation System

### Collaborative Filtering for Product Recommendations
**Krishna's Implementation:**
I built a recommendation system that suggested products to customers based on their purchase history and similar customers. It increased cross-sell by about 12%.

```python
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix

def build_recommendation_system(transactions):
    """
    Build collaborative filtering recommendation system
    This ran daily in production
    """
    # Create user-item matrix
    user_item_matrix = transactions.pivot_table(
        index='customer_id',
        columns='product_id',
        values='quantity',
        aggfunc='sum',
        fill_value=0
    )
    
    # Convert to sparse matrix for memory efficiency
    sparse_matrix = csr_matrix(user_item_matrix.values)
    
    # Calculate item-item similarity
    item_similarity = cosine_similarity(sparse_matrix.T)
    item_similarity_df = pd.DataFrame(
        item_similarity,
        index=user_item_matrix.columns,
        columns=user_item_matrix.columns
    )
    
    return user_item_matrix, item_similarity_df

def get_recommendations(customer_id, user_item_matrix, item_similarity_df, n_recommendations=5):
    """
    Get top N product recommendations for a customer
    """
    # Get products customer has already purchased
    customer_purchases = user_item_matrix.loc[customer_id]
    purchased_products = customer_purchases[customer_purchases > 0].index.tolist()
    
    # Calculate recommendation scores
    recommendation_scores = {}
    for product in purchased_products:
        similar_products = item_similarity_df[product].sort_values(ascending=False)[1:11]
        for similar_product, similarity in similar_products.items():
            if similar_product not in purchased_products:
                if similar_product not in recommendation_scores:
                    recommendation_scores[similar_product] = 0
                recommendation_scores[similar_product] += similarity
    
    # Sort and return top N
    recommendations = sorted(
        recommendation_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:n_recommendations]
    
    return [product for product, score in recommendations]

# Build system
user_item_matrix, item_similarity_df = build_recommendation_system(transactions)

# Get recommendations for a customer
customer_id = 12345
recommendations = get_recommendations(customer_id, user_item_matrix, item_similarity_df)
print(f"Recommendations for customer {customer_id}: {recommendations}")
```

## Model Deployment and Monitoring

### Production ML Pipeline
**Krishna's MLOps Setup:**
So one thing I learned was that training the model is just 20% of the work. The real challenge was deploying it and monitoring it in production.

```python
import joblib
import json
from datetime import datetime
import logging

class ModelMonitor:
    """
    Monitor model performance in production
    I set this up to track model drift
    """
    def __init__(self, model_name):
        self.model_name = model_name
        self.predictions_log = []
        self.performance_log = []
        
        logging.basicConfig(
            filename=f'{model_name}_monitor.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def log_prediction(self, features, prediction, actual=None):
        """Log each prediction for monitoring"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'features': features.tolist() if hasattr(features, 'tolist') else features,
            'prediction': float(prediction),
            'actual': float(actual) if actual is not None else None
        }
        
        self.predictions_log.append(log_entry)
        logging.info(f"Prediction: {json.dumps(log_entry)}")
        
        # Check for data drift
        if len(self.predictions_log) % 1000 == 0:
            self.check_data_drift()
    
    def check_data_drift(self):
        """Check if feature distributions are changing"""
        recent_predictions = self.predictions_log[-1000:]
        
        # Simple check - you'd want something more sophisticated in production
        recent_features = [p['features'] for p in recent_predictions]
        feature_means = np.mean(recent_features, axis=0)
        
        logging.info(f"Recent feature means: {feature_means}")
        
        # Alert if significant drift detected
        # In production, I used more sophisticated drift detection
        
    def calculate_performance(self):
        """Calculate model performance on recent predictions"""
        recent_with_actuals = [
            p for p in self.predictions_log[-1000:]
            if p['actual'] is not None
        ]
        
        if len(recent_with_actuals) > 0:
            predictions = [p['prediction'] for p in recent_with_actuals]
            actuals = [p['actual'] for p in recent_with_actuals]
            
            mae = mean_absolute_error(actuals, predictions)
            rmse = np.sqrt(mean_squared_error(actuals, predictions))
            
            logging.info(f"Recent performance - MAE: {mae:.3f}, RMSE: {rmse:.3f}")
            
            return {'mae': mae, 'rmse': rmse}
        
        return None

# Save model for production
def save_model_for_production(model, scaler, feature_names, model_name):
    """
    Save model with all necessary artifacts
    """
    model_artifacts = {
        'model': model,
        'scaler': scaler,
        'feature_names': feature_names,
        'model_version': '1.0',
        'training_date': datetime.now().isoformat(),
        'model_type': type(model).__name__
    }
    
    joblib.dump(model_artifacts, f'{model_name}_v1.0.pkl')
    print(f"Model saved: {model_name}_v1.0.pkl")

# Load model in production
def load_model_for_inference(model_path):
    """Load model and all artifacts"""
    artifacts = joblib.load(model_path)
    return artifacts

# Example usage
monitor = ModelMonitor('churn_prediction')

# In production API
def predict_churn(customer_features):
    """Production prediction endpoint"""
    # Load model
    artifacts = load_model_for_inference('churn_prediction_v1.0.pkl')
    model = artifacts['model']
    scaler = artifacts['scaler']
    
    # Prepare features
    features_scaled = scaler.transform([customer_features])
    
    # Predict
    prediction = model.predict_proba(features_scaled)[0][1]
    
    # Log prediction
    monitor.log_prediction(customer_features, prediction)
    
    return {
        'customer_id': customer_features[0],
        'churn_probability': float(prediction),
        'risk_level': 'high' if prediction > 0.7 else 'medium' if prediction > 0.4 else 'low'
    }
```

## Real-World Challenges and Solutions

### Handling Imbalanced Data
**Krishna's Experience:**
So one big challenge I faced was imbalanced data. Like in churn prediction, only 5% of customers actually churned. Here's what worked for me:

```python
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline as ImbPipeline

# What I found worked best was a combination of SMOTE and undersampling
def handle_imbalanced_data(X_train, y_train):
    """
    Handle imbalanced dataset
    I tried multiple approaches and this worked best
    """
    # Check class distribution
    print(f"Original class distribution: {np.bincount(y_train)}")
    
    # SMOTE + Random Undersampling
    over = SMOTE(sampling_strategy=0.5, random_state=42)  # Oversample minority to 50%
    under = RandomUnderSampler(sampling_strategy=0.8, random_state=42)  # Undersample majority
    
    steps = [('over', over), ('under', under)]
    pipeline = ImbPipeline(steps=steps)
    
    X_resampled, y_resampled = pipeline.fit_resample(X_train, y_train)
    
    print(f"Resampled class distribution: {np.bincount(y_resampled)}")
    
    return X_resampled, y_resampled

# Use class weights as alternative
model = RandomForestClassifier(
    n_estimators=100,
    class_weight='balanced',  # This helped a lot
    random_state=42
)
```

### Feature Selection
**Krishna's Approach:**
```python
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.ensemble import RandomForestClassifier

def select_best_features(X, y, n_features=20):
    """
    Select most important features
    This reduced training time by 40% without hurting accuracy
    """
    # Method 1: Statistical test
    selector_stats = SelectKBest(score_func=f_classif, k=n_features)
    selector_stats.fit(X, y)
    
    # Method 2: Recursive Feature Elimination
    estimator = RandomForestClassifier(n_estimators=50, random_state=42)
    selector_rfe = RFE(estimator, n_features_to_select=n_features, step=1)
    selector_rfe.fit(X, y)
    
    # Get feature rankings
    feature_scores = pd.DataFrame({
        'feature': X.columns,
        'stats_score': selector_stats.scores_,
        'rfe_ranking': selector_rfe.ranking_
    })
    
    # Select features that rank high in both methods
    top_features = feature_scores.nsmallest(n_features, 'rfe_ranking')['feature'].tolist()
    
    return top_features, feature_scores

# Apply feature selection
top_features, feature_scores = select_best_features(X_train, y_train, n_features=20)
X_train_selected = X_train[top_features]
X_test_selected = X_test[top_features]

print(f"Reduced features from {X_train.shape[1]} to {len(top_features)}")
```

## Interview Talking Points

### Technical Achievements:
- Built churn prediction model reducing customer churn by 15%
- Developed demand forecasting system reducing stockouts by 30%
- Implemented recommendation system increasing cross-sell by 12%
- Achieved 0.87 ROC-AUC score on production churn model
- Reduced model training time by 40% through feature selection

### Technologies Used:
- **ML Libraries**: Scikit-learn, XGBoost, LightGBM, Statsmodels
- **Data Processing**: Pandas, NumPy, SciPy
- **Model Deployment**: Joblib, Flask, Docker
- **Monitoring**: Custom logging, Prometheus, Grafana
- **Cloud**: AWS SageMaker, Azure ML

### Problem-Solving Examples:
- Handled imbalanced data using SMOTE and class weights
- Dealt with data drift by implementing monitoring and retraining pipelines
- Optimized model performance through hyperparameter tuning
- Reduced inference latency from 500ms to 50ms through optimization
