import matplotlib.pyplot as plt
import numpy as np

class LinearRegression:
    def __init__(self, learning_rate=0.01, epochs=1000):
        self.lr = learning_rate
        self.epochs = epochs
        self.beta0 = 0  # intercept
        self.beta1 = 0  # slope
        self.losses = []

    def fit(self, X, y):
        N = len(X)
        self.losses = []
        for epoch in range(self.epochs):
            # Forward pass
            y_pred = self.beta0 + self.beta1 * X
            # Compute loss
            loss = np.mean((y - y_pred) ** 2)
            self.losses.append(loss)
            # Compute gradients
            d_beta0 = -2 * np.mean(y - y_pred)
            d_beta1 = -2 * np.mean((y - y_pred) * X)
            # Update parameters
            self.beta0 -= self.lr * d_beta0
            self.beta1 -= self.lr * d_beta1

    def predict(self, X):
        return self.beta0 + self.beta1 * X

# Generate synthetic data
np.random.seed(42)
X = np.linspace(0, 10, 100)
y = 3 + 2 * X + np.random.randn(100)  # True: beta0=3, beta1=2

# Fit models with different learning rates
learning_rates = [0.001, 0.01, 0.1]
models = []

plt.figure(figsize=(18, 5))

# 1. Scatter plot with fitted lines
plt.subplot(1, 3, 1)
plt.scatter(X, y, alpha=0.5, label='Data')
for lr in learning_rates:
    model = LinearRegression(learning_rate=lr, epochs=1000)
    model.fit(X, y)
    models.append(model)
    plt.plot(X, model.predict(X), label=f'LR={lr}, b0={model.beta0:.2f}, b1={model.beta1:.2f}')
plt.title('Data and Fitted Lines')
plt.legend()

# 2. Loss curves over epochs
plt.subplot(1, 3, 2)
for model, lr in zip(models, learning_rates):
    plt.plot(model.losses, label=f'LR={lr}')
plt.title('Loss over Epochs')
plt.xlabel('Epoch')
plt.ylabel('MSE Loss')
plt.legend()

# 3. Comparison of final predictions (scatter)
plt.subplot(1, 3, 3)
for model, lr in zip(models, learning_rates):
    plt.plot(X, model.predict(X), label=f'LR={lr}')
plt.scatter(X, y, alpha=0.3)
plt.title('Comparison of Learning Rates')
plt.legend()

plt.tight_layout()
plt.show()

# Report learned parameters
for lr, model in zip(learning_rates, models):
    print(f"Learning rate {lr}: beta0={model.beta0:.2f}, beta1={model.beta1:.2f} (True: beta0=3, beta1=2)")
