import torch.nn as nn

class WeatherPredictor(nn.Module):
    def __init__(self, input_size, hidden_size1, hidden_size2, output_size):
        """
        Args:
        input_size (int): Number of input features
        hidden_size1 (int): Number of neurons in first hidden layer
        hidden_size2 (int): Number of neurons in second hidden layer
        output_size (int): Number of output predictions
        """
        super(WeatherPredictor, self).__init__()
        
        # Define layers
        self.fc1 = nn.Linear(input_size, hidden_size1)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size1, hidden_size2)
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(hidden_size2, output_size)
    
    def forward(self, x):
        """
        Forward pass through the network
        
        Args:
        x (torch.Tensor): Input tensor
        
        Returns:
        torch.Tensor: Output predictions
        """
        x = self.fc1(x)
        x = self.relu1(x)
        x = self.fc2(x)
        x = self.relu2(x)
        x = self.fc3(x)
        return x


