import os
import json 
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

# --- 1. CONFIGURATION & HYPERPARAMETERS ---
current_dir = os.getcwd()
data_dir = os.path.join(current_dir, 'Week 5', 'data', 'archive', 'chest_xray')

# Directory to save all outputs
output_dir = os.path.join(current_dir, 'Week 5', 'outputs')
os.makedirs(output_dir, exist_ok=True)

img_size = 150
batch_size = 32
epochs = 12

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# --- 2. DATA AUGMENTATION & LOADERS ---
print("Configuring Data Augmentation and Loaders...")
train_transforms = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((img_size, img_size)),
    transforms.RandomRotation(30),
    transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.8, 1.2)),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
])

test_transforms = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((img_size, img_size)),
    transforms.ToTensor(),
])

train_dataset = datasets.ImageFolder(os.path.join(data_dir, 'train'), transform=train_transforms)
val_dataset = datasets.ImageFolder(os.path.join(data_dir, 'val'), transform=test_transforms)
test_dataset = datasets.ImageFolder(os.path.join(data_dir, 'test'), transform=test_transforms)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

class_names = train_dataset.classes # Expected: ['NORMAL', 'PNEUMONIA']

# --- 3. MODEL ARCHITECTURE ---
class PneumoniaCNN(nn.Module):
    def __init__(self):
        super(PneumoniaCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.drop1 = nn.Dropout2d(0.1)
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1)
        self.bn3 = nn.BatchNorm2d(64)
        self.conv4 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        self.drop2 = nn.Dropout2d(0.2)
        self.bn4 = nn.BatchNorm2d(128)
        self.conv5 = nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1)
        self.drop3 = nn.Dropout2d(0.2)
        self.bn5 = nn.BatchNorm2d(256)
        
        self.fc1 = nn.Linear(256 * 5 * 5, 128)
        self.drop4 = nn.Dropout(0.2)
        self.fc2 = nn.Linear(128, 1)

    def forward(self, x):
        x = F.max_pool2d(F.relu(self.bn1(self.conv1(x))), kernel_size=2, stride=2, padding=0)
        x = self.bn2(self.drop1(F.relu(self.conv2(x))))
        x = F.max_pool2d(x, kernel_size=2, stride=2, padding=1)
        x = F.max_pool2d(F.relu(self.bn3(self.conv3(x))), kernel_size=2, stride=2, padding=0)
        x = self.bn4(self.drop2(F.relu(self.conv4(x))))
        x = F.max_pool2d(x, kernel_size=2, stride=2, padding=1)
        x = self.bn5(self.drop3(F.relu(self.conv5(x))))
        x = F.max_pool2d(x, kernel_size=2, stride=2, padding=0)
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.drop4(x)
        x = self.fc2(x)
        return x

model = PneumoniaCNN().to(device)

# --- 4. LOSS, OPTIMIZER & SCHEDULER ---
criterion = nn.BCEWithLogitsLoss()
optimizer = optim.RMSprop(model.parameters(), lr=0.001)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.3, patience=2, min_lr=0.000001, verbose=True)

# --- 5. TRAINING LOOP ---
print("Starting Training...")
history = {'loss': [], 'accuracy': [], 'val_loss': [], 'val_accuracy': []}

for epoch in range(epochs):
    model.train()
    train_loss, train_correct, train_total = 0.0, 0, 0
    
    for images, labels in train_loader:
        images, labels = images.to(device), labels.float().to(device)
        
        optimizer.zero_grad()
        outputs = model(images).squeeze(1)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        train_loss += loss.item() * images.size(0)
        preds = torch.sigmoid(outputs) >= 0.5
        train_correct += (preds == labels).sum().item()
        train_total += labels.size(0)
        
    epoch_train_loss = train_loss / train_total
    epoch_train_acc = train_correct / train_total
    
    model.eval()
    val_loss, val_correct, val_total = 0.0, 0, 0
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.float().to(device)
            outputs = model(images).squeeze(1)
            loss = criterion(outputs, labels)
            
            val_loss += loss.item() * images.size(0)
            preds = torch.sigmoid(outputs) >= 0.5
            val_correct += (preds == labels).sum().item()
            val_total += labels.size(0)
            
    epoch_val_loss = val_loss / val_total
    epoch_val_acc = val_correct / val_total
    
    history['loss'].append(epoch_train_loss)
    history['accuracy'].append(epoch_train_acc)
    history['val_loss'].append(epoch_val_loss)
    history['val_accuracy'].append(epoch_val_acc)
    
    print(f"Epoch {epoch+1}/{epochs} - "
          f"loss: {epoch_train_loss:.4f} - accuracy: {epoch_train_acc:.4f} - "
          f"val_loss: {epoch_val_loss:.4f} - val_accuracy: {epoch_val_acc:.4f}")
    
    scheduler.step(epoch_val_acc)

#  Save the Model Weights
model_save_path = os.path.join(output_dir, 'pneumonia_cnn_model_2.pth')
torch.save(model.state_dict(), model_save_path)
print(f"Model saved to {model_save_path}")

#  Save the Training Logs (History)
logs_save_path = os.path.join(output_dir, 'training_logs.json')
with open(logs_save_path, 'w') as f:
    json.dump(history, f)
print(f"Training logs saved to {logs_save_path}")


# --- 6. EVALUATION ---
print("\nEvaluating on Test Set...")
model.eval()
test_loss, test_correct, test_total = 0.0, 0, 0
all_preds = []
all_labels = []

with torch.no_grad():
    for images, labels in test_loader:
        images, labels = images.to(device), labels.float().to(device)
        outputs = model(images).squeeze(1)
        loss = criterion(outputs, labels)
        
        test_loss += loss.item() * images.size(0)
        preds = (torch.sigmoid(outputs) >= 0.5).float()
        
        test_correct += (preds == labels).sum().item()
        test_total += labels.size(0)
        
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

final_test_loss = test_loss / test_total
final_test_acc = test_correct / test_total

print(f"Loss of the model is - {final_test_loss:.4f}")
print(f"Accuracy of the model is - {final_test_acc*100:.2f} %")

# --- Save Classification Report ---
# 1. Generate the standard text report
report_str = classification_report(all_labels, all_preds, target_names=class_names)
print("\nClassification Report:")
print(report_str)

# Save as a readable text file
text_report_path = os.path.join(output_dir, 'classification_report.txt')
with open(text_report_path, 'w') as f:
    f.write(report_str)
print(f"Classification report (text) saved to {text_report_path}")

# 2. Generate the dictionary version and save as JSON
report_dict = classification_report(all_labels, all_preds, target_names=class_names, output_dict=True)
json_report_path = os.path.join(output_dir, 'classification_report.json')
with open(json_report_path, 'w') as f:
    # indent=4 makes the JSON file neatly formatted and readable
    json.dump(report_dict, f, indent=4) 
print(f"Classification report (JSON) saved to {json_report_path}")

#  Save Confusion Matrix
cm = confusion_matrix(all_labels, all_preds)
plt.figure(figsize=(8,6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
plt.title('Confusion Matrix')
plt.ylabel('Actual')
plt.xlabel('Predicted')
cm_save_path = os.path.join(output_dir, 'confusion_matrix.png')
plt.savefig(cm_save_path) # Save before showing
print(f"Confusion matrix saved to {cm_save_path}")
plt.show()

#  Save Accuracy and Loss Plot
fig, ax = plt.subplots(1, 2, figsize=(20, 10))
ax[0].plot(history['accuracy'], 'go-', label='Training Accuracy')
ax[0].plot(history['val_accuracy'], 'ro-', label='Validation Accuracy')
ax[0].set_title('Training & Validation Accuracy')
ax[0].legend()
ax[0].set_xlabel("Epochs")
ax[0].set_ylabel("Accuracy")

ax[1].plot(history['loss'], 'go-', label='Training Loss')
ax[1].plot(history['val_loss'], 'ro-', label='Validation Loss')
ax[1].set_title('Training & Validation Loss')
ax[1].legend()
ax[1].set_xlabel("Epochs")
ax[1].set_ylabel("Loss")

plots_save_path = os.path.join(output_dir, 'training_plots.png')
plt.savefig(plots_save_path) 
print(f"Training plots saved to {plots_save_path}")
plt.show()