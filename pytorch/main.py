import torch
import torch.nn as nn
import torch.optim as optim
import sys
import os

# Add the project root to Python path FIRST
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')  # Go up one level from controllers
sys.path.insert(0, project_root)

from model import WeatherPredictor
from data import train_loader, test_loader, scaler_X, scaler_y
from utils import predict_temperature, plot_results


# Initialize the model
input_size = 4 # temperature, humidity, wind_speed, pressure
hidden_size1 = 64
hidden_size2 = 32
output_size = 1 # next day temperature

model = WeatherPredictor(input_size, hidden_size1, hidden_size2, output_size)
print(model)

# Loss function for regression
criterion = nn.MSELoss()
# Optimizer - Adam is a good default choice
optimizer = optim.Adam(model.parameters(), lr=0.001)
# Learning rate scheduler (optional but recommended)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(
 optimizer, mode='min', factor=0.5, patience=5
)


# Save the model
torch.save({
 'model_state_dict': model.state_dict(),
 'optimizer_state_dict': optimizer.state_dict(),
 'scaler_X': scaler_X,
 'scaler_y': scaler_y,
}, 'weather_predictor.pth')
print("Model saved successfully!")
# Load the model
def load_model(filepath, input_size, hidden_size1, hidden_size2, output_size):
    """Load a saved model"""
    checkpoint = torch.load(filepath)
    
    model = WeatherPredictor(input_size, hidden_size1, hidden_size2, output_size)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    return model, checkpoint['scaler_X'], checkpoint['scaler_y']
# Example: Load the model
# loaded_model, loaded_scaler_X, loaded_scaler_y = load_model(
# 'weather_predictor.pth', 4, 64, 32, 1
# )

from train import train_model, evaluate_model
train_losses = train_model(model, train_loader, criterion, optimizer, num_epochs=100)
test_loss, predictions, actuals = evaluate_model(model, test_loader, criterion)

# Predict
from utils import predict_temperature
temp = predict_temperature(model, scaler_X, scaler_y, 22.5, 65, 10, 1013)
print("Predicted temp:", temp)

# Plot training and evaluation results
plot_results(train_losses, actuals, predictions)

# Example prediction
temp = predict_temperature(model, scaler_X, scaler_y, 22.5, 65, 10, 1013)
print(f"Predicted temp: {temp:.2f}°C")

# if __name__ == "__main__":
#     main()
