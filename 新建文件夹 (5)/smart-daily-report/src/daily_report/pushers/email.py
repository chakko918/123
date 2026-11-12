"""SMTP 邮件推送器。未配置或 mock 模式下降级 dry-run。"""
from __future__ import annotations

import logging

from .base import Pusher

logger = logging.getLogger(__name__)


class EmailPusher(Pusher):
    channel = "email"

    def __init__(
        self,
        host: str = "",
        port: int = 465,
        user: str = "",
        password: str = "",
        to: list[str] | None = None,
        mock: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.to = to or []
        self.mock = mock

    def _push(self, content: str, date: str) -> bool:
        subject = f"团队日报 {date}"
        if self.mock or not self.host or not self.to:
            logger.info(
                "[email][dry-run] 未真实发送。主题=%s 正文=%d 字 收件人=%s",
                subject, len(content), self.to or "无",
            )
            return True

        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.user
        msg["To"] = ", ".join(self.to)
        msg.set_content(content)

        with smtplib.SMTP_SSL(self.host, self.port, timeout=10) as server:
            if self.user and self.password:
                server.login(self.user, self.password)
            server.send_message(msg)
        logger.info("[email] 已发送至 %s", self.to)
        return True
