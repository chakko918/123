"""端到端集成测试：覆盖 proposal 成功标准 S1–S4、S7–S10。"""
from daily_report import db
from daily_report.main import run


def test_full_pipeline_mock(tmp_path):
    db_path = tmp_path / "it.db"
    code = run(["--mock", "--date", "2026-11-11", "--db", str(db_path)])
    assert code == 0

    history = db.list_history(db_path)
    assert len(history) == 1
    assert history[0]["date"] == "2026-11-11"
    # S7/S8 降级通道：mock 下两通道 dry-run 均成功
    assert "email" in history[0]["channels"]
    assert "feishu" in history[0]["channels"]


def test_repeated_run_upsert(tmp_path):
    db_path = tmp_path / "it.db"
    run(["--mock", "--date", "2026-11-11", "--db", str(db_path)])
    run(["--mock", "--date", "2026-11-11", "--db", str(db_path)])
    assert len(db.list_history(db_path)) == 1  # S10 幂等
