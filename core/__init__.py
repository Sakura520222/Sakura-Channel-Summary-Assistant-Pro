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
Core模块 - 项目核心功能
所有Python模块都集中在core目录下
"""

# AI客户端
from . import ai_client

# 配置管理
from . import config
from . import config_validators

# 数据库
from . import database

# 错误处理
from . import error_handler

# 历史记录处理
from . import history_handlers

# 日志配置
from . import logger_config

# 提示词管理
from . import prompt_manager
from . import poll_prompt_manager

# 投票重新生成处理
from . import poll_regeneration_handlers

# 调度器
from . import scheduler

# 总结时间管理
from . import summary_time_manager

# Telegram客户端工具
from . import telegram_client_utils
from . import telegram_client

# Telegram模块（包含子模块）
from .telegram import (
    fetch_last_week_messages,
    send_report,
    send_long_message,
    send_poll,
    extract_date_range_from_summary,
    set_active_client,
    get_active_client
)

# 命令处理器（包含子模块）
from .command_handlers import (
    handle_manual_summary,
    handle_show_prompt,
    handle_set_prompt,
    handle_prompt_input,
    handle_show_poll_prompt,
    handle_set_poll_prompt,
    handle_poll_prompt_input,
    handle_show_log_level,
    handle_set_log_level,
    handle_restart,
    handle_show_channels,
    handle_add_channel,
    handle_delete_channel,
    handle_clear_summary_time,
    handle_set_send_to_source,
    handle_show_channel_schedule,
    handle_set_channel_schedule,
    handle_delete_channel_schedule,
    handle_changelog,
    handle_shutdown,
    handle_pause,
    handle_resume,
    handle_start,
    handle_help,
    handle_clear_cache,
    handle_clean_logs,
    handle_blacklist
)

__all__ = [
    # AI客户端
    'ai_client',
    
    # 配置管理
    'config',
    'config_validators',
    
    # 数据库
    'database',
    
    # 错误处理
    'error_handler',
    
    # 历史记录处理
    'history_handlers',
    
    # 日志配置
    'logger_config',
    
    # 提示词管理
    'prompt_manager',
    'poll_prompt_manager',
    
    # 投票重新生成处理
    'poll_regeneration_handlers',
    
    # 调度器
    'scheduler',
    
    # 总结时间管理
    'summary_time_manager',
    
    # Telegram客户端工具
    'telegram_client_utils',
    'telegram_client',
    
    # Telegram模块导出的函数
    'fetch_last_week_messages',
    'send_report',
    'send_long_message',
    'send_poll',
    'extract_date_range_from_summary',
    'set_active_client',
    'get_active_client',
    
    # 命令处理器导出的函数
    'handle_manual_summary',
    'handle_show_prompt',
    'handle_set_prompt',
    'handle_prompt_input',
    'handle_show_poll_prompt',
    'handle_set_poll_prompt',
    'handle_poll_prompt_input',
    'handle_show_log_level',
    'handle_set_log_level',
    'handle_restart',
    'handle_show_channels',
    'handle_add_channel',
    'handle_delete_channel',
    'handle_clear_summary_time',
    'handle_set_send_to_source',
    'handle_show_channel_schedule',
    'handle_set_channel_schedule',
    'handle_delete_channel_schedule',
    'handle_changelog',
    'handle_shutdown',
    'handle_pause',
    'handle_resume',
    'handle_start',
    'handle_help',
    'handle_clear_cache',
    'handle_clean_logs',
    'handle_blacklist'
]
