import torch
import numpy as np

def train_model(model, train_loader, criterion, optimizer, num_epochs=100):
    """
    Train the neural network
    
    Args:
    model: Neural network model
    train_loader: DataLoader for training data
    criterion: Loss function
    optimizer: Optimization algorithm
    num_epochs: Number of training epochs
    
    Returns:
    list: Training losses per epoch
    """
    train_losses = []
    
    for epoch in range(num_epochs):
        model.train() # Set model to training mode
        running_loss = 0.0
    
        for inputs, targets in train_loader:
            # Zero the gradients
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(inputs)
            
            # Calculate loss
            loss = criterion(outputs, targets)
            
            # Backward pass
            loss.backward()
            
            # Update weights
            optimizer.step()
            
            running_loss += loss.item()
        
        # Calculate average loss for this epoch
        epoch_loss = running_loss / len(train_loader)
        train_losses.append(epoch_loss)
        
        # Print progress
        if (epoch + 1) % 10 == 0:
            print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss:.4f}')
        
    return train_losses
    # Train the model
    num_epochs = 100
    train_losses = train_model(model, train_loader, criterion, optimizer, num_epochs)

def evaluate_model(model, test_loader, criterion):
    """
    Evaluate the model on test data
    
    Args:
    model: Trained neural network
    test_loader: DataLoader for test data
    criterion: Loss function
    
    Returns:
    float: Average test loss
    """
    model.eval() # Set model to evaluation mode
    test_loss = 0.0
    predictions = []
    actuals = []
        
    with torch.no_grad(): # Disable gradient computation
        for inputs, targets in test_loader:
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            test_loss += loss.item()
                
            predictions.extend(outputs.numpy())
            actuals.extend(targets.numpy())
        
    avg_test_loss = test_loss / len(test_loader)

    return avg_test_loss, np.array(predictions), np.array(actuals)

    # Evaluate the model
    test_loss, predictions, actuals = evaluate_model(model, test_loader, criterion)
    print(f'\nTest Loss: {test_loss:.4f}')
    # Inverse transform to get actual temperature values
    predictions_orig = scaler_y.inverse_transform(predictions)
    actuals_orig = scaler_y.inverse_transform(actuals)
    # Calculate metrics in original scale
    mae = np.mean(np.abs(predictions_orig - actuals_orig))
    rmse = np.sqrt(np.mean((predictions_orig - actuals_orig)**2))
    print(f'Mean Absolute Error: {mae:.2f}°C')
    print(f'Root Mean Squared Error: {rmse:.2f}°C')
