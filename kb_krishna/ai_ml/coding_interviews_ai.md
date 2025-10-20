---
tags: [ai-ml, coding, interview, python, algorithms, data-structures, machine-learning]
persona: ai
---

# AI/ML Coding Interview Guide - Krishna's Approach

## Introduction
**Krishna's Coding Interview Philosophy:**
Having solved hundreds of coding problems and built production AI systems, I approach coding interviews by focusing on clean, efficient solutions with clear explanations. My experience with Python, data structures, and ML algorithms gives me practical insights into solving problems that mirror real-world AI/ML challenges.

## Core Python Skills for AI/ML

### 1. Data Structures & Algorithms
**Krishna's Essential Patterns:**

#### Arrays & Lists
```python
# Two Pointers Technique
def two_sum(nums, target):
    """Find two numbers that add up to target"""
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

# Sliding Window
def max_sum_subarray(nums, k):
    """Find maximum sum of subarray of size k"""
    if len(nums) < k:
        return 0
    
    window_sum = sum(nums[:k])
    max_sum = window_sum
    
    for i in range(k, len(nums)):
        window_sum = window_sum - nums[i-k] + nums[i]
        max_sum = max(max_sum, window_sum)
    
    return max_sum
```

#### Hash Tables & Dictionaries
```python
# Character Frequency
def character_frequency(s):
    """Count character frequencies"""
    freq = {}
    for char in s:
        freq[char] = freq.get(char, 0) + 1
    return freq

# Group Anagrams
def group_anagrams(strs):
    """Group strings that are anagrams"""
    groups = {}
    for s in strs:
        key = ''.join(sorted(s))
        if key not in groups:
            groups[key] = []
        groups[key].append(s)
    return list(groups.values())
```

#### Trees & Graphs
```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

# Binary Tree Traversal
def inorder_traversal(root):
    """Inorder traversal of binary tree"""
    result = []
    
    def traverse(node):
        if node:
            traverse(node.left)
            result.append(node.val)
            traverse(node.right)
    
    traverse(root)
    return result

# BFS for Graphs
def bfs(graph, start):
    """Breadth-first search"""
    visited = set()
    queue = [start]
    result = []
    
    while queue:
        node = queue.pop(0)
        if node not in visited:
            visited.add(node)
            result.append(node)
            queue.extend(graph[node])
    
    return result
```

### 2. Machine Learning Algorithms Implementation
**Krishna's ML Coding Examples:**

#### Linear Regression from Scratch
```python
import numpy as np

class LinearRegression:
    def __init__(self, learning_rate=0.01, max_iterations=1000):
        self.learning_rate = learning_rate
        self.max_iterations = max_iterations
        self.weights = None
        self.bias = None
    
    def fit(self, X, y):
        """Train the model using gradient descent"""
        n_samples, n_features = X.shape
        self.weights = np.zeros(n_features)
        self.bias = 0
        
        for _ in range(self.max_iterations):
            # Predictions
            y_pred = X.dot(self.weights) + self.bias
            
            # Compute gradients
            dw = (1/n_samples) * X.T.dot(y_pred - y)
            db = (1/n_samples) * np.sum(y_pred - y)
            
            # Update parameters
            self.weights -= self.learning_rate * dw
            self.bias -= self.learning_rate * db
    
    def predict(self, X):
        """Make predictions"""
        return X.dot(self.weights) + self.bias
```

#### K-Means Clustering
```python
import numpy as np
from sklearn.metrics.pairwise import euclidean_distances

class KMeans:
    def __init__(self, k=3, max_iters=100):
        self.k = k
        self.max_iters = max_iters
        self.centroids = None
        self.labels = None
    
    def fit(self, X):
        """Fit K-means clustering"""
        n_samples, n_features = X.shape
        
        # Initialize centroids randomly
        self.centroids = X[np.random.choice(n_samples, self.k, replace=False)]
        
        for _ in range(self.max_iters):
            # Assign points to closest centroid
            distances = euclidean_distances(X, self.centroids)
            self.labels = np.argmin(distances, axis=1)
            
            # Update centroids
            new_centroids = np.array([X[self.labels == i].mean(axis=0) 
                                    for i in range(self.k)])
            
            # Check for convergence
            if np.allclose(self.centroids, new_centroids):
                break
            
            self.centroids = new_centroids
    
    def predict(self, X):
        """Predict cluster for new data"""
        distances = euclidean_distances(X, self.centroids)
        return np.argmin(distances, axis=1)
```

### 3. Data Processing & Feature Engineering
**Krishna's Data Processing Patterns:**

#### Text Preprocessing
```python
import re
import string
from collections import Counter

def preprocess_text(text):
    """Clean and preprocess text for ML"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_features(text):
    """Extract features from text"""
    words = text.split()
    
    features = {
        'word_count': len(words),
        'char_count': len(text),
        'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
        'unique_words': len(set(words)),
        'most_common_word': Counter(words).most_common(1)[0][0] if words else None
    }
    
    return features
```

#### Time Series Processing
```python
import pandas as pd
import numpy as np

def create_time_features(df, date_col):
    """Create time-based features"""
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    df['year'] = df[date_col].dt.year
    df['month'] = df[date_col].dt.month
    df['day'] = df[date_col].dt.day
    df['dayofweek'] = df[date_col].dt.dayofweek
    df['is_weekend'] = df['dayofweek'].isin([5, 6])
    df['quarter'] = df[date_col].dt.quarter
    
    return df

def create_lag_features(df, target_col, lags=[1, 7, 30]):
    """Create lag features for time series"""
    df = df.copy()
    for lag in lags:
        df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
    
    return df
```

## Common AI/ML Coding Problems

### Problem 1: Implement a Recommendation System
```python
import numpy as np
from scipy.sparse import csr_matrix

class CollaborativeFiltering:
    def __init__(self, n_factors=50, learning_rate=0.01, regularization=0.01):
        self.n_factors = n_factors
        self.learning_rate = learning_rate
        self.regularization = regularization
        self.user_factors = None
        self.item_factors = None
    
    def fit(self, user_item_matrix):
        """Train collaborative filtering model"""
        n_users, n_items = user_item_matrix.shape
        
        # Initialize factors randomly
        self.user_factors = np.random.normal(0, 0.1, (n_users, self.n_factors))
        self.item_factors = np.random.normal(0, 0.1, (n_items, self.n_factors))
        
        # Convert to sparse matrix for efficiency
        matrix = csr_matrix(user_item_matrix)
        
        # Gradient descent
        for epoch in range(100):
            for u in range(n_users):
                for i in range(n_items):
                    if matrix[u, i] > 0:  # Only for observed ratings
                        prediction = np.dot(self.user_factors[u], self.item_factors[i])
                        error = matrix[u, i] - prediction
                        
                        # Update factors
                        self.user_factors[u] += self.learning_rate * (
                            error * self.item_factors[i] - 
                            self.regularization * self.user_factors[u]
                        )
                        self.item_factors[i] += self.learning_rate * (
                            error * self.user_factors[u] - 
                            self.regularization * self.item_factors[i]
                        )
    
    def predict(self, user_id, item_id):
        """Predict rating for user-item pair"""
        return np.dot(self.user_factors[user_id], self.item_factors[item_id])
```

### Problem 2: Implement Text Classification
```python
from collections import defaultdict
import math

class NaiveBayesClassifier:
    def __init__(self):
        self.word_counts = defaultdict(lambda: defaultdict(int))
        self.class_counts = defaultdict(int)
        self.vocabulary = set()
    
    def fit(self, texts, labels):
        """Train Naive Bayes classifier"""
        for text, label in zip(texts, labels):
            words = self.preprocess_text(text)
            self.class_counts[label] += 1
            
            for word in words:
                self.word_counts[label][word] += 1
                self.vocabulary.add(word)
    
    def preprocess_text(self, text):
        """Simple text preprocessing"""
        return text.lower().split()
    
    def predict(self, text):
        """Predict class for text"""
        words = self.preprocess_text(text)
        total_docs = sum(self.class_counts.values())
        
        best_class = None
        best_score = float('-inf')
        
        for class_label in self.class_counts:
            # Prior probability
            prior = math.log(self.class_counts[class_label] / total_docs)
            
            # Likelihood
            likelihood = 0
            for word in words:
                if word in self.vocabulary:
                    word_count = self.word_counts[class_label][word]
                    total_words = sum(self.word_counts[class_label].values())
                    likelihood += math.log((word_count + 1) / (total_words + len(self.vocabulary)))
            
            score = prior + likelihood
            
            if score > best_score:
                best_score = score
                best_class = class_label
        
        return best_class
```

### Problem 3: Implement Data Pipeline
```python
import pandas as pd
import numpy as np
from typing import List, Dict, Any

class DataPipeline:
    def __init__(self):
        self.transformations = []
        self.validators = []
    
    def add_transformation(self, func, name=None):
        """Add transformation step"""
        self.transformations.append({
            'func': func,
            'name': name or func.__name__
        })
        return self
    
    def add_validator(self, func, name=None):
        """Add validation step"""
        self.validators.append({
            'func': func,
            'name': name or func.__name__
        })
        return self
    
    def process(self, data):
        """Process data through pipeline"""
        result = data.copy()
        
        # Apply transformations
        for step in self.transformations:
            try:
                result = step['func'](result)
                print(f"✓ {step['name']} completed")
            except Exception as e:
                print(f"✗ {step['name']} failed: {e}")
                raise
        
        # Apply validations
        for validator in self.validators:
            try:
                validator['func'](result)
                print(f"✓ {validator['name']} passed")
            except Exception as e:
                print(f"✗ {validator['name']} failed: {e}")
                raise
        
        return result

# Example usage
def clean_data(df):
    """Clean data transformation"""
    return df.dropna().reset_index(drop=True)

def validate_data(df):
    """Validate data quality"""
    if df.empty:
        raise ValueError("Data is empty")
    if df.isnull().any().any():
        raise ValueError("Data contains null values")
    return True

# Create pipeline
pipeline = (DataPipeline()
    .add_transformation(clean_data, "Data Cleaning")
    .add_validator(validate_data, "Data Validation")
)
```

## Krishna's Coding Interview Tips

### 1. Problem-Solving Approach
- **Understand the problem**: Ask clarifying questions
- **Think out loud**: Explain your thought process
- **Start simple**: Begin with brute force, then optimize
- **Test your solution**: Walk through examples

### 2. Code Quality
- **Clean code**: Use meaningful variable names
- **Handle edge cases**: Consider empty inputs, single elements
- **Add comments**: Explain complex logic
- **Optimize**: Discuss time/space complexity

### 3. Communication
- **Explain your approach**: Before coding
- **Discuss trade-offs**: Time vs. space complexity
- **Ask questions**: Clarify requirements
- **Think about scale**: How would this work with large data?

### 4. Common Patterns
- **Two pointers**: For sorted arrays
- **Sliding window**: For subarray problems
- **Hash tables**: For lookups and counting
- **Dynamic programming**: For optimization problems

This coding approach has helped me successfully solve technical challenges in AI/ML interviews and build production systems at Walgreens.
