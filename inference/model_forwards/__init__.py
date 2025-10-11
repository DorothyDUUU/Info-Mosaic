import os
import importlib
import glob

# Get all .py files in the models directory (excluding __init__.py)
model_files = glob.glob(os.path.join(os.path.dirname(__file__), "*.py"))
model_files = [f for f in model_files if not f.endswith("__init__.py")]

# Dynamically import each model file
for model_file in model_files:
    module_name = os.path.splitext(os.path.basename(model_file))[0]
    importlib.import_module(f"inference.model_forwards.{module_name}")
