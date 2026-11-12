from daily_report.pushers import EmailPusher, FeishuBotPusher


def test_email_dry_run_returns_true():
    assert EmailPusher(mock=True).push("content", "2026-11-11") is True


def test_email_unconfigured_returns_true():
    assert EmailPusher(host="", to=[], mock=False).push("content", "2026-11-11") is True


def test_feishu_dry_run_returns_true():
    assert FeishuBotPusher(mock=True).push("content", "2026-11-11") is True


def test_pusher_exception_returns_false():
    class Broken(FeishuBotPusher):
        def _push(self, content, date):
            raise RuntimeError("boom")

    assert Broken(webhook="x", mock=False).push("content", "2026-11-11") is False
