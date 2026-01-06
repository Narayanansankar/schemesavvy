import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torchbnn as bnn
import matplotlib.pyplot as plt
from sklearn import datasets

# Load data
data, target = datasets.load_iris(return_X_y=True)
data_tensor, target_tensor = torch.from_numpy(data).float(), torch.from_numpy(target).long()

# Model
model = nn.Sequential(
    bnn.BayesLinear(4, 100, prior_mu=0, prior_sigma=0.1),
    nn.ReLU(),
    bnn.BayesLinear(100, 3, prior_mu=0, prior_sigma=0.1)
)

# Loss and optimizer
cross_entropy_loss = nn.CrossEntropyLoss()
klloss = bnn.BKLLoss(reduction='mean', last_layer_only=False)
optimizer = optim.Adam(model.parameters(), lr=0.01)

# Training loop
for step in range(3000):
    output = model(data_tensor)
    loss = cross_entropy_loss(output, target_tensor) + 0.01 * klloss(model)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if step % 100 == 0:
        accuracy = (torch.max(output.data, 1)[1] == target_tensor).float().mean().item()
        print(f'- Accuracy: {accuracy * 100:.2f}%, CE: {loss.item():.2f}, KL: {klloss(model).item():.2f}')

# Visualization
def draw_graph(predicted):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    ax1.scatter(data[:, 0], data[:, 1], c=target, marker='v')
    ax2.scatter(data[:, 0], data[:, 1], c=predicted)
    ax1.set_title("REAL")
    ax2.set_title("PREDICT")
    plt.colorbar(ax1.collections[0], ax=ax1)
    plt.colorbar(ax2.collections[0], ax=ax2)
    plt.show()

# Predictions and visualization
_, predicted = torch.max(model(data_tensor).data, 1)
draw_graph(predicted)
