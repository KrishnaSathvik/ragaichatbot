---
tags: [deep-learning, nlp, tensorflow, keras, pytorch, transformers, bert, text-processing]
persona: ai
---

# Deep Learning & NLP Projects - Krishna's Experience

## Text Classification for Customer Feedback

### Sentiment Analysis Pipeline
**Krishna's Implementation:**
So at Walgreens, we were getting thousands of customer reviews and feedback every day. I built this NLP pipeline to automatically classify them as positive, negative, or neutral. It actually helped the customer service team prioritize issues way better.

```python
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download required NLTK data
nltk.download('stopwords')
nltk.download('punkt')

def preprocess_text(text):
    """
    Clean and preprocess text data
    This is what I used in production
    """
    # Lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    
    # Remove special characters and digits
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    
    # Join back
    return ' '.join(tokens)

# Load and preprocess data
df = pd.read_csv('customer_feedback.csv')
df['cleaned_text'] = df['feedback_text'].apply(preprocess_text)

print(f"Total feedback: {len(df)}")
print(f"Sentiment distribution:\n{df['sentiment'].value_counts()}")

# Prepare data
X = df['cleaned_text'].values
y = df['sentiment'].values

# Encode labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
```

### Building LSTM Model
**Krishna's Deep Learning Approach:**
```python
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# Tokenization
max_words = 10000
max_len = 200

tokenizer = Tokenizer(num_words=max_words, oov_token='<OOV>')
tokenizer.fit_on_texts(X_train)

# Convert text to sequences
X_train_seq = tokenizer.texts_to_sequences(X_train)
X_test_seq = tokenizer.texts_to_sequences(X_test)

# Pad sequences
X_train_pad = pad_sequences(X_train_seq, maxlen=max_len, padding='post', truncating='post')
X_test_pad = pad_sequences(X_test_seq, maxlen=max_len, padding='post', truncating='post')

print(f"Training sequences shape: {X_train_pad.shape}")
print(f"Testing sequences shape: {X_test_pad.shape}")

# Build LSTM model
def build_lstm_model(vocab_size, embedding_dim=128, max_len=200, num_classes=3):
    """
    Build LSTM model for sentiment classification
    This architecture worked really well for me
    """
    model = keras.Sequential([
        # Embedding layer
        layers.Embedding(vocab_size, embedding_dim, input_length=max_len),
        
        # Spatial dropout to prevent overfitting
        layers.SpatialDropout1D(0.2),
        
        # Bidirectional LSTM - this helped capture context better
        layers.Bidirectional(layers.LSTM(64, return_sequences=True)),
        layers.Dropout(0.3),
        
        # Another LSTM layer
        layers.Bidirectional(layers.LSTM(32)),
        layers.Dropout(0.3),
        
        # Dense layers
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.3),
        
        # Output layer
        layers.Dense(num_classes, activation='softmax')
    ])
    
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

# Create model
model = build_lstm_model(
    vocab_size=max_words,
    embedding_dim=128,
    max_len=max_len,
    num_classes=len(label_encoder.classes_)
)

model.summary()

# Callbacks
early_stopping = EarlyStopping(
    monitor='val_loss',
    patience=3,
    restore_best_weights=True
)

checkpoint = ModelCheckpoint(
    'best_sentiment_model.h5',
    monitor='val_accuracy',
    save_best_only=True,
    verbose=1
)

# Train model
history = model.fit(
    X_train_pad, y_train,
    validation_split=0.2,
    epochs=20,
    batch_size=32,
    callbacks=[early_stopping, checkpoint],
    verbose=1
)

# Evaluate
test_loss, test_accuracy = model.evaluate(X_test_pad, y_test)
print(f"\nTest Accuracy: {test_accuracy:.4f}")
print(f"Test Loss: {test_loss:.4f}")
```

### Using Pre-trained BERT
**Krishna's Transfer Learning Approach:**
So I also tried using BERT and it actually performed better than my LSTM model. The accuracy went from 85% to 91%.

```python
from transformers import BertTokenizer, TFBertForSequenceClassification
from transformers import InputExample, InputFeatures
import tensorflow as tf

# Load pre-trained BERT
model_name = 'bert-base-uncased'
tokenizer = BertTokenizer.from_pretrained(model_name)
bert_model = TFBertForSequenceClassification.from_pretrained(
    model_name,
    num_labels=len(label_encoder.classes_)
)

def convert_data_to_examples(texts, labels):
    """Convert text data to BERT input format"""
    examples = []
    for text, label in zip(texts, labels):
        examples.append(
            InputExample(guid=None, text_a=text, text_b=None, label=label)
        )
    return examples

def convert_examples_to_tf_dataset(examples, tokenizer, max_length=128):
    """Convert examples to TensorFlow dataset"""
    features = []
    
    for example in examples:
        input_dict = tokenizer.encode_plus(
            example.text_a,
            add_special_tokens=True,
            max_length=max_length,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='tf'
        )
        
        features.append({
            'input_ids': input_dict['input_ids'].numpy()[0],
            'attention_mask': input_dict['attention_mask'].numpy()[0],
            'label': example.label
        })
    
    def gen():
        for feature in features:
            yield (
                {
                    'input_ids': feature['input_ids'],
                    'attention_mask': feature['attention_mask']
                },
                feature['label']
            )
    
    return tf.data.Dataset.from_generator(
        gen,
        ({'input_ids': tf.int32, 'attention_mask': tf.int32}, tf.int64),
        (
            {
                'input_ids': tf.TensorShape([None]),
                'attention_mask': tf.TensorShape([None])
            },
            tf.TensorShape([])
        )
    )

# Prepare data for BERT
train_examples = convert_data_to_examples(X_train, y_train)
test_examples = convert_data_to_examples(X_test, y_test)

train_dataset = convert_examples_to_tf_dataset(train_examples, tokenizer)
test_dataset = convert_examples_to_tf_dataset(test_examples, tokenizer)

train_dataset = train_dataset.shuffle(100).batch(16).repeat(2)
test_dataset = test_dataset.batch(16)

# Fine-tune BERT
optimizer = tf.keras.optimizers.Adam(learning_rate=2e-5)
loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
bert_model.compile(optimizer=optimizer, loss=loss, metrics=['accuracy'])

# Train
history = bert_model.fit(
    train_dataset,
    validation_data=test_dataset,
    epochs=3,  # BERT fine-tuning usually needs fewer epochs
    verbose=1
)

print(f"BERT model achieved {history.history['val_accuracy'][-1]:.4f} validation accuracy")
```

## Named Entity Recognition (NER)

### Custom NER for Medical Text
**Krishna's Healthcare NER Project:**
```python
import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
import random

def train_custom_ner(training_data, model=None, n_iter=30):
    """
    Train custom NER model for medical entities
    I used this to extract drug names and dosages from prescriptions
    """
    # Create blank model or load existing
    if model is not None:
        nlp = spacy.load(model)
    else:
        nlp = spacy.blank("en")
    
    # Add NER pipeline if it doesn't exist
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner")
    else:
        ner = nlp.get_pipe("ner")
    
    # Add labels
    for _, annotations in training_data:
        for ent in annotations.get("entities"):
            ner.add_label(ent[2])
    
    # Disable other pipes during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.begin_training()
        
        for iteration in range(n_iter):
            random.shuffle(training_data)
            losses = {}
            
            # Batch the examples
            batches = minibatch(training_data, size=compounding(4.0, 32.0, 1.001))
            
            for batch in batches:
                examples = []
                for text, annotations in batch:
                    doc = nlp.make_doc(text)
                    example = Example.from_dict(doc, annotations)
                    examples.append(example)
                
                nlp.update(examples, drop=0.5, losses=losses)
            
            print(f"Iteration {iteration + 1}, Losses: {losses}")
    
    return nlp

# Training data format
TRAIN_DATA = [
    ("Patient prescribed Metformin 500mg twice daily", {
        "entities": [(19, 28, "DRUG"), (29, 35, "DOSAGE")]
    }),
    ("Take Lisinopril 10mg once per day", {
        "entities": [(5, 15, "DRUG"), (16, 20, "DOSAGE")]
    }),
    # More training examples...
]

# Train model
nlp_ner = train_custom_ner(TRAIN_DATA, n_iter=30)

# Save model
nlp_ner.to_disk("medical_ner_model")

# Use model for prediction
def extract_medical_entities(text):
    """Extract medical entities from text"""
    doc = nlp_ner(text)
    entities = []
    for ent in doc.ents:
        entities.append({
            'text': ent.text,
            'label': ent.label_,
            'start': ent.start_char,
            'end': ent.end_char
        })
    return entities

# Test
test_text = "Patient should take Aspirin 81mg daily and Atorvastatin 20mg at bedtime"
entities = extract_medical_entities(test_text)
print(f"Extracted entities: {entities}")
```

## Text Generation and Summarization

### Document Summarization
**Krishna's Approach:**
```python
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

def summarize_documents(documents, max_length=150, min_length=50):
    """
    Summarize long documents
    I used this to summarize customer feedback reports
    """
    # Load pre-trained summarization model
    model_name = "facebook/bart-large-cnn"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    
    summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)
    
    summaries = []
    for doc in documents:
        # Truncate if too long
        if len(doc.split()) > 1024:
            doc = ' '.join(doc.split()[:1024])
        
        summary = summarizer(
            doc,
            max_length=max_length,
            min_length=min_length,
            do_sample=False
        )
        
        summaries.append(summary[0]['summary_text'])
    
    return summaries

# Example usage
long_feedback = """
Customer called regarding prescription refill delay. They mentioned waiting for 3 days 
without receiving notification. The customer was frustrated but remained polite throughout 
the conversation. They expressed concern about running out of medication. After checking 
the system, we found the prescription was pending doctor approval. We expedited the 
approval process and offered same-day pickup. Customer was satisfied with the resolution 
and thanked the team for quick action.
"""

summary = summarize_documents([long_feedback])
print(f"Summary: {summary[0]}")
```

## Production Deployment

### FastAPI Service for NLP Models
**Krishna's Production Setup:**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import tensorflow as tf
from transformers import pipeline
import joblib
import numpy as np

app = FastAPI(title="NLP Service API")

# Load models at startup
sentiment_model = None
tokenizer = None
summarizer = None

@app.on_event("startup")
async def load_models():
    """Load all models when service starts"""
    global sentiment_model, tokenizer, summarizer
    
    # Load sentiment model
    sentiment_model = tf.keras.models.load_model('best_sentiment_model.h5')
    tokenizer = joblib.load('tokenizer.pkl')
    
    # Load summarization model
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    
    print("All models loaded successfully")

class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    text: str
    sentiment: str
    confidence: float

@app.post("/predict/sentiment", response_model=SentimentResponse)
async def predict_sentiment(request: SentimentRequest):
    """
    Predict sentiment of text
    This endpoint handles 1000+ requests per day
    """
    try:
        # Preprocess
        cleaned_text = preprocess_text(request.text)
        
        # Tokenize and pad
        sequence = tokenizer.texts_to_sequences([cleaned_text])
        padded = tf.keras.preprocessing.sequence.pad_sequences(
            sequence, maxlen=200, padding='post'
        )
        
        # Predict
        prediction = sentiment_model.predict(padded)
        sentiment_idx = np.argmax(prediction[0])
        confidence = float(prediction[0][sentiment_idx])
        
        sentiments = ['negative', 'neutral', 'positive']
        sentiment = sentiments[sentiment_idx]
        
        return SentimentResponse(
            text=request.text,
            sentiment=sentiment,
            confidence=confidence
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SummarizationRequest(BaseModel):
    text: str
    max_length: int = 150
    min_length: int = 50

class SummarizationResponse(BaseModel):
    original_text: str
    summary: str
    compression_ratio: float

@app.post("/summarize", response_model=SummarizationResponse)
async def summarize_text(request: SummarizationRequest):
    """Summarize long text"""
    try:
        summary = summarizer(
            request.text,
            max_length=request.max_length,
            min_length=request.min_length,
            do_sample=False
        )
        
        summary_text = summary[0]['summary_text']
        compression_ratio = len(summary_text) / len(request.text)
        
        return SummarizationResponse(
            original_text=request.text,
            summary=summary_text,
            compression_ratio=compression_ratio
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models_loaded": sentiment_model is not None and summarizer is not None
    }

# Run with: uvicorn nlp_service:app --host 0.0.0.0 --port 8000
```

## Real-World Challenges

### Handling Multiple Languages
**Krishna's Solution:**
```python
from langdetect import detect
from transformers import MarianMTModel, MarianTokenizer

def detect_and_translate(text, target_lang='en'):
    """
    Detect language and translate if needed
    We had customers submitting feedback in Spanish
    """
    try:
        source_lang = detect(text)
        
        if source_lang == target_lang:
            return text, source_lang
        
        # Load translation model
        model_name = f'Helsinki-NLP/opus-mt-{source_lang}-{target_lang}'
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        
        # Translate
        translated = model.generate(**tokenizer(text, return_tensors="pt", padding=True))
        translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
        
        return translated_text, source_lang
    
    except Exception as e:
        print(f"Translation error: {e}")
        return text, 'unknown'
```

## Interview Talking Points

### Technical Achievements:
- Built sentiment analysis model with 91% accuracy using BERT
- Deployed NLP service handling 1000+ requests daily
- Implemented custom NER model for medical text extraction
- Reduced manual review time by 70% through automated classification
- Achieved 85% accuracy on LSTM model, improved to 91% with BERT

### Technologies Used:
- **Deep Learning**: TensorFlow, Keras, PyTorch
- **NLP**: Transformers, BERT, spaCy, NLTK
- **Deployment**: FastAPI, Docker, Kubernetes
- **Cloud**: AWS SageMaker, Azure ML
- **Monitoring**: Prometheus, Grafana, CloudWatch

### Problem-Solving Examples:
- Handled imbalanced text data using data augmentation
- Optimized inference latency from 2s to 200ms
- Implemented multilingual support for customer feedback
- Dealt with model drift by implementing retraining pipelines
