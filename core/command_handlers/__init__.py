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

from .system_commands import (
    handle_show_log_level, handle_set_log_level,
    handle_restart, handle_changelog, handle_shutdown,
    handle_pause, handle_resume, handle_clean_logs,
    handle_help, handle_start, handle_clear_cache, handle_blacklist,
    handle_reload
)
from .channel_commands import (
    handle_show_channels, handle_add_channel, handle_delete_channel,
    handle_show_channel_schedule, handle_set_channel_schedule,
    handle_delete_channel_schedule, handle_clear_summary_time,
    handle_set_send_to_source, handle_channel_poll,
    handle_set_channel_poll, handle_delete_channel_poll
)
from .summary_commands import handle_manual_summary
from .prompt_commands import (
    handle_show_prompt, handle_set_prompt, handle_prompt_input,
    handle_show_poll_prompt, handle_set_poll_prompt,
    handle_poll_prompt_input
)

__all__ = [
    'handle_show_log_level', 'handle_set_log_level',
    'handle_restart', 'handle_changelog', 'handle_shutdown',
    'handle_pause', 'handle_resume', 'handle_clean_logs',
    'handle_help', 'handle_start', 'handle_clear_cache',
    'handle_blacklist', 'handle_reload',
    'handle_show_channels', 'handle_add_channel', 'handle_delete_channel',
    'handle_show_channel_schedule', 'handle_set_channel_schedule',
    'handle_delete_channel_schedule', 'handle_clear_summary_time',
    'handle_set_send_to_source', 'handle_channel_poll',
    'handle_set_channel_poll', 'handle_delete_channel_poll',
    'handle_manual_summary',
    'handle_show_prompt', 'handle_set_prompt', 'handle_prompt_input',
    'handle_show_poll_prompt', 'handle_set_poll_prompt',
    'handle_poll_prompt_input',
]
