import subprocess
import sys
import os

def install_requirements(requirements_file="requirements.txt"):
    if not os.path.exists(requirements_file):
        print(f"Файл {requirements_file} не знайдено.")
        return
    
    with open(requirements_file, "r") as f:
        packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    for package in packages:
        print(f"Встановлюю {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if __name__ == "__main__":
    install_requirements()