import os
import importlib
import glob

# 获取 models 目录下所有 .py 文件（排除 __init__.py）
model_files = glob.glob(os.path.join(os.path.dirname(__file__), "*.py"))
model_files = [f for f in model_files if not f.endswith("__init__.py")]

# 动态导入每个模型文件
for model_file in model_files:
    module_name = os.path.splitext(os.path.basename(model_file))[0]
    importlib.import_module(f"evaluation.model_forwards.{module_name}")