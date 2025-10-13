import matplotlib.pyplot as plt
import numpy as np
import torch


def plot_results(train_losses, actuals_orig, predictions_orig):
    """
    Plot training loss and predictions vs actual values.
    """
    plt.figure(figsize=(12, 4))

    # Plot training loss
    plt.subplot(1, 2, 1)
    plt.plot(train_losses)
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training Loss Over Time')
    plt.grid(True)

    # Plot predictions vs actual
    plt.subplot(1, 2, 2)
    plt.scatter(actuals_orig, predictions_orig, alpha=0.5)
    plt.plot([actuals_orig.min(), actuals_orig.max()],
             [actuals_orig.min(), actuals_orig.max()],
             'r--', lw=2, label='Perfect Prediction')
    plt.xlabel('Actual Temperature (°C)')
    plt.ylabel('Predicted Temperature (°C)')
    plt.title('Predictions vs Actual Values')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def predict_temperature(model, scaler_X, scaler_y, temp, humidity, wind_speed, pressure):
    """
    Predict tomorrow's temperature given current weather conditions.
    """
    model.eval()

    input_data = np.array([[temp, humidity, wind_speed, pressure]])
    input_scaled = scaler_X.transform(input_data)
    input_tensor = torch.FloatTensor(input_scaled)

    with torch.no_grad():
        prediction_scaled = model(input_tensor)
        prediction = scaler_y.inverse_transform(prediction_scaled.numpy())

    return prediction[0][0]
