# PyTorch Setup Instructions

## Problem
There seems to be an issue with the PyTorch installation in the main Python environment, where it's trying to load CUDA libraries but encountering errors. This might be due to a mismatch between the installed PyTorch version and the system's CUDA version.

## Solution
We've created a separate virtual environment with a CPU-only version of PyTorch that works correctly. You can use this environment to run your code that depends on PyTorch.

## Setup
1. If you haven't already, run the setup script to create the virtual environment:
   ```bash
   python setup_torch_env.py
   ```
   This will create a virtual environment in the `torch_venv` directory with a working installation of PyTorch.

## Usage Options

### Option 1: Use the Runner Script
To run any Python script with the PyTorch virtual environment, use:
```bash
python run_with_torch_venv.py your_script.py [args]
```

For example:
```bash
python run_with_torch_venv.py main.py
```

### Option 2: Activate the Virtual Environment
Alternatively, you can activate the virtual environment and then run your scripts directly:

```bash
# On Windows
torch_venv\Scripts\activate

# On macOS/Linux
source torch_venv/bin/activate

# Then run your scripts
python main.py
```

## Debugging
If you encounter any issues, try running a simple test to check if PyTorch is working:
```bash
python run_with_torch_venv.py simple_torch_test.py
```

## Understanding the NumPy Warning
You may see a warning about NumPy 2.1.2 compatibility. This is an informational warning and doesn't affect the functionality of PyTorch for basic operations. The tests we've run confirm that PyTorch is working correctly despite this warning.

## Next Steps
1. For long-term usage, consider fixing the system-wide PyTorch installation by:
   - Uninstalling PyTorch completely: `pip uninstall -y torch torchvision torchaudio`
   - Installing a compatible version that matches your CUDA version
   - If you need CUDA support, make sure to install PyTorch with the correct CUDA version that matches your system

2. If you decide to fix the system-wide installation, check your CUDA version with `nvidia-smi` and then use the appropriate installation command from [PyTorch's website](https://pytorch.org/get-started/locally/). 