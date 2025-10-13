from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Set random seed for reproducibility
torch.manual_seed(42)
np.random.seed(42)

# Generate synthetic weather data
n_samples = 1000

# Features: temperature, humidity, wind_speed, pressure
temperature = np.random.uniform(0, 35, n_samples)
humidity = np.random.uniform(30, 90, n_samples)
wind_speed = np.random.uniform(0, 25, n_samples)
pressure = np.random.uniform(980, 1040, n_samples)

# Target: tomorrow's temperature (with some correlation to today's weather)
next_day_temp = (0.7 * temperature +
 0.1 * (humidity - 60) / 30 * 5 +
 np.random.normal(0, 2, n_samples))

# Create DataFrame
data = pd.DataFrame({
    'temperature': temperature,
    'humidity': humidity,
    'wind_speed': wind_speed,
    'pressure': pressure,
    'next_day_temp': next_day_temp
})

print(data.head())
print(f"\nDataset shape: {data.shape}")


class WeatherDataset(Dataset):
    def __init__(self, features, targets):
        """
        Args:
        features (numpy.ndarray): Input features
        targets (numpy.ndarray): Target values
        """
        self.features = torch.FloatTensor(features)
        self.targets = torch.FloatTensor(targets)
        
    def __len__(self):
        return len(self.features)
        
    def __getitem__(self, idx):
        return self.features[idx], self.targets[idx]


# Split features and target
X = data[['temperature', 'humidity', 'wind_speed', 'pressure']].values
y = data['next_day_temp'].values.reshape(-1, 1)

# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(
 X, y, test_size=0.2, random_state=42
)

# Normalize features
scaler_X = StandardScaler()
scaler_y = StandardScaler()
X_train_scaled = scaler_X.fit_transform(X_train)
X_test_scaled = scaler_X.transform(X_test)
y_train_scaled = scaler_y.fit_transform(y_train)
y_test_scaled = scaler_y.transform(y_test)

# Create datasets
train_dataset = WeatherDataset(X_train_scaled, y_train_scaled)
test_dataset = WeatherDataset(X_test_scaled, y_test_scaled)

# Create data loaders
batch_size = 32
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

print(f"Training samples: {len(train_dataset)}")
print(f"Test samples: {len(test_dataset)}")