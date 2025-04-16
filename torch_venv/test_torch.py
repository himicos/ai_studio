
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

# Test a simple tensor operation
x = torch.tensor([1, 2, 3])
print(f"Test tensor: {x}")
print(f"Test operation: {x + 1}")
