import subprocess
import sys
import os
from pathlib import Path

def main():
    # Get the path to the Python executable in the virtual environment
    venv_dir = Path("torch_venv")
    if not venv_dir.exists():
        print("Virtual environment not found. Please run setup_torch_env.py first.")
        return
    
    if sys.platform == "win32":
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
    
    if len(sys.argv) < 2:
        print("Usage: python run_with_torch_venv.py <script.py> [arg1 arg2 ...]")
        return
    
    script_path = sys.argv[1]
    args = sys.argv[2:]
    
    # Run the specified script with the Python from the virtual environment
    cmd = [str(python_exe), script_path] + args
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 