import torch
import sys

print(f"Python version: {sys.version}")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

# Create a tensor
x = torch.tensor([[1, 2, 3], [4, 5, 6]])
print(f"Tensor shape: {x.shape}")
print(f"Tensor data:\n{x}")

# Simple operations
y = x + 10
print(f"x + 10 =\n{y}")

# Matrix multiplication
z = torch.matmul(x, x.T)
print(f"x * x.T =\n{z}")

print("PyTorch is working correctly!") 