import sys
from pathlib import Path

# Automatically add apps/api and packages/options-alpha-mcp to sys.path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))
sys.path.insert(0, str(ROOT_DIR / "packages" / "options-alpha-mcp"))
