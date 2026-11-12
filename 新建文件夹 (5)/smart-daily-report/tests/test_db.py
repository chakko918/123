from daily_report import db


def test_save_and_list(tmp_path):
    db_path = tmp_path / "t.db"
    db.init_db(db_path)
    db.save_report("2026-11-11", "content A", ["email"], db_path=db_path)
    history = db.list_history(db_path)
    assert len(history) == 1
    assert history[0]["date"] == "2026-11-11"
    assert history[0]["channels"] == "email"


def test_upsert_same_date(tmp_path):
    db_path = tmp_path / "t.db"
    db.init_db(db_path)
    db.save_report("2026-11-11", "v1", ["email"], db_path=db_path)
    db.save_report("2026-11-11", "v2", ["email", "feishu"], db_path=db_path)
    history = db.list_history(db_path)
    assert len(history) == 1  # 同日期仅保留最新一份
    assert history[0]["channels"] == "email,feishu"
