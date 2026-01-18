# Copyright 2026 Sakura-频道总结助手
# 
# 本项目采用 GNU General Public License v3.0 (GPLv3) 许可证
# 
# 您可以自由地：
# - 商业使用：将本软件用于商业目的
# - 修改：将本软件以满足您的需求
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

"""配置重载通知模块

提供配置重载成功/失败的 Telegram 通知功能。
"""

import logging
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Optional

from .config_watcher import ReloadResult
from .config import ADMIN_LIST, logger

# 最大消息长度（Telegram 限制）
MAX_MESSAGE_LENGTH = 4000

# 频率限制：最小发送间隔（秒）
MIN_NOTIFICATION_INTERVAL = 10.0

# 最后通知时间（用于频率限制）
_last_notification_time = 0.0

logger = logging.getLogger(__name__)


def escape_markdown(text: str) -> str:
    """转义 Markdown 特殊字符
    
    Args:
        text: 原始文本
        
    Returns:
        转义后的文本
    """
    if not text:
        return text
    
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def escape_html(text: str) -> str:
    """转义 HTML 特殊字符
    
    Args:
        text: 原始文本
        
    Returns:
        转义后的文本
    """
    if not text:
        return text
    
    return (text.replace('&', '&')
                .replace('<', '<')
                .replace('>', '>'))


def format_value_diff(old_value, new_value, value_name: str) -> str:
    """格式化值变更对比
    
    Args:
        old_value: 旧值
        new_value: 新值
        value_name: 值名称
        
    Returns:
        格式化的对比字符串
    """
    if old_value == new_value:
        return f"{value_name}: {new_value} (无变更)"
    elif new_value > old_value:
        diff = new_value - old_value
        return f"{value_name}: {old_value} -> {new_value} (新增 {diff} 个)"
    else:
        diff = old_value - new_value
        return f"{value_name}: {old_value} -> {new_value} (减少 {diff} 个)"


def format_bool_diff(old_value, new_value, value_name: str) -> str:
    """格式化布尔值变更对比
    
    Args:
        old_value: 旧值
        new_value: 新值
        value_name: 值名称
        
    Returns:
        格式化的对比字符串
    """
    if old_value == new_value:
        return f"{value_name}: {new_value} (无变更)"
    else:
        return f"{value_name}: {old_value} -> {new_value}"


def build_success_notification(result: ReloadResult, is_auto_reload: bool = False) -> str:
    """构建成功通知消息
    
    Args:
        result: 重载结果
        is_auto_reload: 是否为自动重载
        
    Returns:
        格式化的通知消息
    """
    # 配置类型映射
    config_type_names = {
        'env': '环境变量配置',
        'config': 'JSON配置',
        'prompt': '总结提示词',
        'poll_prompt': '投票提示词'
    }
    
    config_name = config_type_names.get(result.config_type, result.config_type)
    
    # 构建消息标题
    if is_auto_reload:
        title = "🔔 配置已自动重载"
    else:
        title = "🔔 配置重载通知"
    
    message = f"{title}\n\n"
    
    # 成功状态
    message += f"✅ **{config_name}重载成功**\n\n"
    
    # 变更详情
    if result.old_values and result.details:
        message += "**变更详情:**\n"
        
        # 对比各个配置项
        old_values = result.old_values
        new_values = result.details
        
        # 频道列表对比
        if 'channels' in new_values:
            old_count = old_values.get('channels', 0)
            new_count = new_values.get('channels', 0)
            message += f"- {format_value_diff(old_count, new_count, '频道列表')}\n"
        
        # 总结时间配置对比
        if 'summary_schedules' in new_values:
            old_count = old_values.get('summary_schedules', 0)
            new_count = new_values.get('summary_schedules', 0)
            message += f"- {format_value_diff(old_count, new_count, '总结时间配置')}\n"
        
        # 投票配置对比
        if 'poll_settings' in new_values:
            old_count = old_values.get('poll_settings', 0)
            new_count = new_values.get('poll_settings', 0)
            message += f"- {format_value_diff(old_count, new_count, '投票配置')}\n"
        
        # 发送报告到源频道配置对比
        if 'send_report_to_source' in new_values:
            old_value = old_values.get('send_report_to_source', False)
            new_value = new_values.get('send_report_to_source', False)
            message += f"- {format_bool_diff(old_value, new_value, '发送报告到源频道')}\n"
        
        # 启用投票配置对比
        if 'enable_poll' in new_values:
            old_value = old_values.get('enable_poll', False)
            new_value = new_values.get('enable_poll', False)
            message += f"- {format_bool_diff(old_value, new_value, '启用投票')}\n"
        
        # 调度器重启状态
        if 'scheduler_restarted' in new_values:
            scheduler_restarted = new_values.get('scheduler_restarted', False)
            if scheduler_restarted:
                message += "- 调度器已重启\n"
        
        message += "\n"
    
    # 提示词长度（仅针对提示词）
    if result.config_type in ('prompt', 'poll_prompt') and result.details:
        length = result.details.get('length', 0)
        message += f"提示词长度: {length} 字符\n\n"
    
    # 日志级别（仅针对环境变量）
    if result.config_type == 'env' and result.details:
        log_level = result.details.get('log_level')
        if log_level:
            message += f"日志级别: {log_level}\n\n"
    
    # 时间戳
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    message += f"时间: {timestamp}"
    
    # 检查消息长度
    if len(message) > MAX_MESSAGE_LENGTH:
        message = message[:MAX_MESSAGE_LENGTH - 3] + "..."
        logger.warning(f"通知消息超长，已截断至 {MAX_MESSAGE_LENGTH} 字符")
    
    return message


def build_failure_notification(result: ReloadResult) -> str:
    """构建失败通知消息
    
    Args:
        result: 重载结果
        
    Returns:
        格式化的通知消息
    """
    # 配置类型映射
    config_type_names = {
        'env': '环境变量配置',
        'config': 'JSON配置',
        'prompt': '总结提示词',
        'poll_prompt': '投票提示词'
    }
    
    config_name = config_type_names.get(result.config_type, result.config_type)
    
    # 构建消息标题
    message = "🔔 配置重载通知\n\n"
    
    # 失败状态
    message += f"❌ **{config_name}重载失败**\n\n"
    
    # 错误详情
    if result.message:
        message += f"**错误:** {escape_markdown(result.message)}\n\n"
    
    # 错误类型和位置
    if result.error_type:
        error_info = result.error_type
        if result.error_location:
            error_info += f" at {result.error_location}"
        message += f"**错误类型:** {error_info}\n\n"
    
    # JSON 解析错误的详细信息
    if hasattr(result, '_last_json_error') and result._last_json_error:
        json_error = result._last_json_error
        if json_error.get('type') == 'JSONDecodeError':
            message += "**错误详情:**\n"
            if 'line' in json_error and json_error['line'] != 'Unknown':
                message += f"- 行: {json_error['line']}\n"
            if 'column' in json_error and json_error['column'] != 'Unknown':
                message += f"- 列: {json_error['column']}\n"
            if 'position' in json_error and json_error['position'] != 'Unknown':
                message += f"- 位置: {json_error['position']}\n"
            if 'message' in json_error:
                # 限制错误消息长度
                error_msg = json_error['message'][:200]
                message += f"- 原因: {escape_markdown(error_msg)}\n"
            message += "\n"
    
    # 建议信息
    if result.config_type == 'config':
        message += "**建议:** 请检查配置文件语法和格式\n\n"
    elif result.config_type in ('prompt', 'poll_prompt'):
        message += "**建议:** 请检查提示词文件是否存在且不为空\n\n"
    
    # 时间戳
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    message += f"时间: {timestamp}"
    
    # 检查消息长度
    if len(message) > MAX_MESSAGE_LENGTH:
        message = message[:MAX_MESSAGE_LENGTH - 3] + "..."
        logger.warning(f"通知消息超长，已截断至 {MAX_MESSAGE_LENGTH} 字符")
    
    return message


def can_send_notification() -> bool:
    """检查是否可以发送通知（频率限制）
    
    Returns:
        是否可以发送
    """
    global _last_notification_time
    
    current_time = time.time()
    elapsed = current_time - _last_notification_time
    
    if elapsed < MIN_NOTIFICATION_INTERVAL:
        logger.info(f"通知发送被频率限制拦截，距离上次发送 {elapsed:.1f} 秒")
        return False
    
    _last_notification_time = current_time
    return True


async def send_reload_notification(result: ReloadResult, is_auto_reload: bool = False):
    """发送配置重载通知到所有管理员
    
    Args:
        result: 重载结果
        is_auto_reload: 是否为自动重载（Watchdog 触发）
    """
    global _last_notification_time
    
    # 频率限制检查
    if is_auto_reload and not can_send_notification():
        return
    
    # 构建通知消息
    if result.success:
        message = build_success_notification(result, is_auto_reload)
    else:
        message = build_failure_notification(result)
    
    # 获取活动客户端
    from .telegram import get_active_client
    client = get_active_client()
    
    if not client:
        logger.warning("没有活动的 Telegram 客户端，无法发送通知")
        return
    
    # 发送给所有管理员
    sent_count = 0
    failed_count = 0
    
    for admin_id in ADMIN_LIST:
        # 类型检查
        if not isinstance(admin_id, int):
            logger.warning(f"管理员 ID 类型错误: {admin_id} ({type(admin_id)})，跳过发送")
            failed_count += 1
            continue
        
        try:
            # 自动重载使用静默模式
            await client.send_message(
                admin_id,
                message,
                link_preview=False,
                silent=is_auto_reload
            )
            sent_count += 1
            logger.debug(f"成功向管理员 {admin_id} 发送配置重载通知")
        except Exception as e:
            failed_count += 1
            logger.error(f"向管理员 {admin_id} 发送通知失败: {type(e).__name__}: {e}")
    
    # 记录发送结果
    if sent_count > 0:
        mode = "自动重载（静默）" if is_auto_reload else "手动重载"
        logger.info(f"配置重载通知已发送（{mode}），成功: {sent_count}，失败: {failed_count}")
    else:
        logger.warning(f"配置重载通知发送失败，所有管理员都发送失败")


def reset_notification_throttle():
    """重置通知频率限制
    
    用于测试或特殊场景，允许立即发送通知。
    """
    global _last_notification_time
    _last_notification_time = 0.0
    logger.info("通知频率限制已重置")
