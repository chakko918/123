"""pytest 根配置：把 src 加入 sys.path，无需安装即可导入 daily_report。"""
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
