from pathlib import Path

views_directory = Path(__file__).parent
for file_path in views_directory.glob("*.py"):
    module_name = file_path.stem
    if module_name != "__init__":
        exec(f"from .{module_name} import *")
