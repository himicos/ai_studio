import subprocess
import sys
import os
from pathlib import Path
import venv

def main():
    # Create a virtual environment
    venv_dir = Path("torch_venv")
    if not venv_dir.exists():
        print(f"Creating virtual environment at {venv_dir}")
        venv.create(venv_dir, with_pip=True)
    else:
        print(f"Using existing virtual environment at {venv_dir}")
    
    # Get the path to the Python executable in the virtual environment
    if sys.platform == "win32":
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
    
    # Install PyTorch with CPU support in the virtual environment
    print("Installing PyTorch CPU version in the virtual environment...")
    subprocess.check_call([
        str(python_exe), "-m", "pip", "install", 
        "torch==2.1.0", "torchvision==0.16.0", "torchaudio==2.1.0", 
        "--index-url", "https://download.pytorch.org/whl/cpu"
    ])
    
    # Create a test script in the virtual environment
    test_script = venv_dir / "test_torch.py"
    with open(test_script, "w") as f:
        f.write("""
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

# Test a simple tensor operation
x = torch.tensor([1, 2, 3])
print(f"Test tensor: {x}")
print(f"Test operation: {x + 1}")
""")
    
    # Run the test script
    print("\nRunning test script in the virtual environment...")
    subprocess.check_call([str(python_exe), str(test_script)])
    
    print("\nSetup complete!")
    print(f"To activate the virtual environment, run:")
    if sys.platform == "win32":
        print(f"{venv_dir}\\Scripts\\activate")
    else:
        print(f"source {venv_dir}/bin/activate")

if __name__ == "__main__":
    main() 