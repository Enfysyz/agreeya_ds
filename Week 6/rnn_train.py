import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
import re
import nltk
from nltk.corpus import stopwords
from sklearn.model_selection import train_test_split
from collections import Counter
import matplotlib.pyplot as plt
nltk.download("stopwords")
import os

from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
from sklearn.utils.class_weight import compute_class_weight
import json


current_dir = os.getcwd()
output_dir = os.path.join(current_dir, 'Week 6', 'output')
os.makedirs(output_dir, exist_ok=True) # Creates the folder if it doesn't exist

data_dir = os.path.join(current_dir, 'Week 6', 'data', 'Reddit_Data.csv', 'Reddit_Data.csv')
df = pd.read_csv(data_dir)

df.dropna(inplace=True)

df['category'] = df['category'].map({-1.0: 0, 0.0: 1, 1.0: 2})

stop_words = set(stopwords.words('english'))

def preprocess(text):
    # Remove non-letters and convert to lowercase
    text = re.sub(r'[^a-zA-Z\s]', '', str(text).lower())
    words = text.split()
    # Remove stopwords
    words = [w for w in words if w not in stop_words]
    return words

df['tokens'] = df['clean_comment'].apply(preprocess)

# Build Vocabulary
all_words = [word for tokens in df['tokens'] for word in tokens]
word_counts = Counter(all_words)

MAX_VOCAB_SIZE = 20000
vocab = {word: idx + 2 for idx, (word, count) in enumerate(word_counts.most_common(MAX_VOCAB_SIZE))}
vocab['<PAD>'] = 0  # Padding token
vocab['<UNK>'] = 1  # Unknown token

# Encode and Pad sequences
MAX_SEQ_LEN = 50

def encode_text(tokens):
    encoded = [vocab.get(word, vocab['<UNK>']) for word in tokens]
    if len(encoded) < MAX_SEQ_LEN:
        encoded += [vocab['<PAD>']] * (MAX_SEQ_LEN - len(encoded))
    else:
        encoded = encoded[:MAX_SEQ_LEN]
    return encoded

df['encoded'] = df['tokens'].apply(encode_text)

class TweetDataset(Dataset):
    def __init__(self, sequences, labels):
        self.sequences = torch.tensor(sequences, dtype=torch.long)
        self.labels = torch.tensor(labels, dtype=torch.long)
        
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]
    

X = np.vstack(df['encoded'].values)
y = df['category'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

train_dataset = TweetDataset(X_train, y_train)
test_dataset = TweetDataset(X_test, y_test)

train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=128)

class SentimentLSTM(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim, n_layers, bidirectional, drop_prob):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, 
                            hidden_dim, 
                            num_layers=n_layers, 
                            bidirectional=bidirectional, 
                            batch_first=True, 
                            dropout=drop_prob if n_layers > 1 else 0)
        self.dropout = nn.Dropout(drop_prob)
        # Multiply hidden_dim by 2 if bidirectional
        self.fc = nn.Linear(hidden_dim * 2 if bidirectional else hidden_dim, output_dim)
        
    def forward(self, text):
        # text: [batch_size, seq_len]
        embedded = self.dropout(self.embedding(text)) 
        
        # lstm_out: [batch_size, seq_len, hidden_dim * 2]
        # hidden: [num_layers * 2, batch_size, hidden_dim]
        lstm_out, (hidden, cell) = self.lstm(embedded)
        
        # Concat the final forward and backward hidden states
        if self.lstm.bidirectional:
            hidden = self.dropout(torch.cat((hidden[-2,:,:], hidden[-1,:,:]), dim=1))
        else:
            hidden = self.dropout(hidden[-1,:,:])
            
        return self.fc(hidden)
    
# Hyperparameters
VOCAB_SIZE = len(vocab)
EMBED_DIM = 128
HIDDEN_DIM = 128
OUTPUT_DIM = 3 
N_LAYERS = 2
BIDIRECTIONAL = True
DROPOUT = 0.3

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

model = SentimentLSTM(VOCAB_SIZE, EMBED_DIM, HIDDEN_DIM, OUTPUT_DIM, N_LAYERS, BIDIRECTIONAL, DROPOUT)
model = model.to(device)

# Calculate weights inversely proportional to class frequencies
class_weights = compute_class_weight(
    class_weight='balanced',
    classes=np.unique(y_train),
    y=y_train
)

# Convert to PyTorch tensor and move to device
weights_tensor = torch.tensor(class_weights, dtype=torch.float).to(device)

# Pass weights into the Loss Function
criterion = nn.CrossEntropyLoss(weight=weights_tensor)
optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)

def train(model, loader, optimizer, criterion):
    model.train()
    epoch_loss = 0
    correct = 0
    total = 0
    for sequences, labels in loader:
        sequences, labels = sequences.to(device), labels.to(device)
        
        optimizer.zero_grad()
        predictions = model(sequences)
        loss = criterion(predictions, labels)
        loss.backward()
        optimizer.step()
        
        epoch_loss += loss.item()
        _, predicted = torch.max(predictions, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
    return epoch_loss / len(loader), correct / total

EPOCHS = 20
training_logs = [] 

for epoch in range(EPOCHS):
    train_loss, train_acc = train(model, train_loader, optimizer, criterion)
    log_line = f'Epoch {epoch+1}/{EPOCHS} | Train Loss: {train_loss:.3f} | Train Acc: {train_acc*100:.2f}%'
    print(log_line)
    
    training_logs.append({
        'epoch': epoch + 1,
        'train_loss': train_loss,
        'train_acc': train_acc
    })

# SAVE TRAINING LOGS 
logs_path = os.path.join(output_dir, 'training_logs.csv')
pd.DataFrame(training_logs).to_csv(logs_path, index=False)
print(f"Training logs saved to {logs_path}")

# SAVE THE MODEL
model_path = os.path.join(output_dir, 'sentiment_lstm_model.pth')
torch.save(model.state_dict(), model_path)
print(f"Model weights saved to {model_path}")

def evaluate(model, loader, criterion):
    model.eval() # Put model in evaluation mode
    epoch_loss = 0
    correct = 0
    total = 0
    
    all_predictions = []
    all_targets = []
    
    with torch.no_grad(): # Disable gradient calculation
        for sequences, labels in loader:
            sequences, labels = sequences.to(device), labels.to(device)
            
            predictions = model(sequences)
            loss = criterion(predictions, labels)
            
            epoch_loss += loss.item()
            _, predicted = torch.max(predictions, 1)
            
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            # Store for scikit-learn metrics
            all_predictions.extend(predicted.cpu().numpy())
            all_targets.extend(labels.cpu().numpy())
            
    return epoch_loss / len(loader), correct / total, all_targets, all_predictions

print("\nEvaluating model on test dataset...")
test_loss, test_acc, true_labels, pred_labels = evaluate(model, test_loader, criterion)
print(f'Test Loss: {test_loss:.3f} | Test Acc: {test_acc*100:.2f}%\n')

target_names = ['Negative (0)', 'Neutral (1)', 'Positive (2)']

# --- GENERATE AND SAVE CLASSIFICATION REPORT ---
report_str = classification_report(true_labels, pred_labels, target_names=target_names)
print("Classification Report:")
print(report_str)

report_path = os.path.join(output_dir, 'classification_report.txt')
with open(report_path, 'w') as f:
    f.write(f"Test Loss: {test_loss:.3f} | Test Acc: {test_acc*100:.2f}%\n\n")
    f.write("Classification Report:\n")
    f.write(report_str)
print(f"Classification report saved to {report_path}")

# --- GENERATE AND SAVE CONFUSION MATRIX PLOT ---
cm = confusion_matrix(true_labels, pred_labels)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=target_names, yticklabels=target_names)
plt.title('Sentiment Analysis Confusion Matrix')
plt.ylabel('Actual Sentiment')
plt.xlabel('Predicted Sentiment')

plot_path = os.path.join(output_dir, 'confusion_matrix.png')
plt.savefig(plot_path, bbox_inches='tight', dpi=300)
