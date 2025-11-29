from .base import Base
import importlib
import pathlib

# 自动导入当前目录下所有模型文件（除了 base.py 和 __init__.py）
model_dir = pathlib.Path(__file__).parent
for file in model_dir.glob("*.py"):
    if file.name not in ("__init__.py", "base.py") and file.suffix == ".py":
        module_name = f"{__name__}.{file.stem}"
        importlib.import_module(module_name)

__all__ = ["Base"]
