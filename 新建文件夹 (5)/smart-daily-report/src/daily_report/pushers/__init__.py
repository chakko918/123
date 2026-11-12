"""推送层：把日报文本推送到不同通道。"""
from .base import Pusher
from .email import EmailPusher
from .feishu_bot import FeishuBotPusher

__all__ = ["Pusher", "EmailPusher", "FeishuBotPusher"]
