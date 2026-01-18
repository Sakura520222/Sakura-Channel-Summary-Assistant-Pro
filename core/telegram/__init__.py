# Copyright 2026 Sakura-频道总结助手
# 
# 本项目采用 GNU General Public License v3.0 (GPLv3) 许可证
# 
# 您可以自由地：
# - 商业使用：将本软件用于商业目的
# - 修改：修改本软件以满足您的需求
# - 分发：分发本软件的副本
# - 专利使用：明确授予专利许可
# 
# 您必须遵守以下条件：
# - 开源修改：如果修改了代码，必须开源修改后的代码
# - 源代码分发：分发程序时必须同时提供源代码
# - 相同许可证：修改和分发必须使用相同的GPLv3许可证
# - 版权声明：保留原有的版权声明和许可证
# 
# 本项目源代码：https://github.com/Sakura520222/Sakura-Channel-Summary-Assistant-Pro
# 许可证全文：https://www.gnu.org/licenses/gpl-3.0.html

"""
Telegram客户端模块
将原本 telegram_client.py 拆分为多个子模块以提高可维护性
"""

# 导入消息抓取相关函数
from .message_fetcher import fetch_last_week_messages

# 导入消息发送相关函数
from .message_sender import (
    send_report,
    send_long_message,
    extract_date_range_from_summary,
    set_active_client,
    get_active_client
)

# 导入投票发送相关函数
from .poll_sender import (
    send_poll,
    send_poll_to_channel,
    send_poll_to_discussion_group
)

__all__ = [
    # 消息抓取
    'fetch_last_week_messages',
    
    # 消息发送
    'send_report',
    'send_long_message',
    'extract_date_range_from_summary',
    'set_active_client',
    'get_active_client',
    
    # 投票发送
    'send_poll',
    'send_poll_to_channel',
    'send_poll_to_discussion_group'
]
