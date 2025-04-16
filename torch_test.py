import os
# Set environment variable to disable CUDA
os.environ["CUDA_VISIBLE_DEVICES"] = ""

try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"Device count: {torch.cuda.device_count()}")
        print(f"Current device: {torch.cuda.current_device()}")
    else:
        print("Running on CPU only")
    
    # Test a simple tensor operation
    x = torch.tensor([1, 2, 3])
    print(f"Test tensor: {x}")
    print(f"Test operation: {x + 1}")
    
except Exception as e:
    print(f"Error importing PyTorch: {e}")
    print("Try reinstalling PyTorch with: pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu")