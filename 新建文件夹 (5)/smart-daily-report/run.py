"""便捷入口：免去 PYTHONPATH，直接运行。

用法（在 smart-daily-report 目录下）：
    python run.py --mock                # mock 模式（无需任何凭证）
    python run.py --no-mock             # 真实接口（需先配好 .env）
    python run.py --check               # 凭证就绪检查
    python run.py --no-mock --date 2026-11-11
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from daily_report.main import run  # noqa: E402

if __name__ == "__main__":
    sys.exit(run())
